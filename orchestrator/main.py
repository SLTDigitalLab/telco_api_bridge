import os
import uvicorn
import json
import asyncio
import sys
import traceback
from urllib.parse import urlparse
from contextlib import AsyncExitStack, asynccontextmanager
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# MCP Imports
from mcp.server import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from openai import AsyncOpenAI
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# --- Configuration ---
MCP_SERVICES = {
    "leave": os.getenv("LEAVE_SERVICE_URL", "http://leave_service:8000/sse"),
    "loan": os.getenv("LOAN_SERVICE_URL", "http://loan_service:8001/sse"),
    "policy": os.getenv("POLICY_SERVICE_URL", "http://policy_service:8002/sse"),
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Global State & Connection Manager ---
class OrchestratorGlobal:
    def __init__(self):
        self.service_tasks: Dict[str, asyncio.Task] = {}
        self.service_stop_events: Dict[str, asyncio.Event] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map: Dict[str, str] = {} # tool_name -> service_name

    async def _manage_service_connection(self, name: str, url: str, stop_event: asyncio.Event, ready_future: asyncio.Future):
        """Background task to maintain connection context."""
        async with AsyncExitStack() as stack:
            try:
                print(f"🔌 (Re)connecting to {name} at {url}...")
                parsed = urlparse(url)
                port = parsed.port
                headers = {"Host": f"localhost:{port}"} if port else {}
                
                read, write = await stack.enter_async_context(
                    sse_client(url, headers=headers, timeout=60.0)
                )
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                
                # Refresh tools for this service
                result = await session.list_tools()
                for tool in result.tools:
                    self.tool_map[tool.name] = name
                    print(f"    - Found tool: {tool.name}")
                
                self.sessions[name] = session
                print(f"Connected to {name}")
                sys.stdout.flush()
                
                if not ready_future.done():
                    ready_future.set_result(True)
                
                # Keep alive until stop requested
                await stop_event.wait()
                print(f"Stopping connection task for {name}")

            except Exception as e:
                print(f"⚠️ Connection error in task for {name}: {e}")
                sys.stdout.flush()
                if not ready_future.done():
                    ready_future.set_exception(e)
            finally:
                if name in self.sessions:
                    del self.sessions[name]

    async def connect_service(self, name: str, url: str) -> Optional[ClientSession]:
        """Connects a single service, managing it in a background task."""
        await self.disconnect_service(name)
        
        stop_event = asyncio.Event()
        loop = asyncio.get_running_loop()
        ready_future = loop.create_future()
        
        task = asyncio.create_task(self._manage_service_connection(name, url, stop_event, ready_future))
        self.service_tasks[name] = task
        self.service_stop_events[name] = stop_event
        
        try:
            await ready_future
            return self.sessions.get(name)
        except Exception as e:
            print(f"⚠️ Failed to connect to {name} ({url}): {e}")
            sys.stdout.flush()
            await self.disconnect_service(name)
            return None

    async def disconnect_service(self, name: str):
        if name in self.service_stop_events:
            self.service_stop_events[name].set()
        
        if name in self.service_tasks:
            task = self.service_tasks.pop(name)
            self.service_stop_events.pop(name, None)
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print(f"Error awaiting disconnect task for {name}: {e}")
        
        if name in self.sessions:
            del self.sessions[name]

    async def get_session(self, name: str) -> Optional[ClientSession]:
        """Get existing session or attempt to connect."""
        if name in self.sessions:
            return self.sessions[name]
        
        url = MCP_SERVICES.get(name)
        if url:
            return await self.connect_service(name, url)
        return None

    async def connect_downstream(self):
        """Initial connection to all services."""
        print("Connecting to all downstream services...")
        sys.stdout.flush()
        tasks = []
        for name, url in MCP_SERVICES.items():
            tasks.append(self.connect_service(name, url))
        await asyncio.gather(*tasks)

    async def cleanup(self):
        print("Closing all downstream connections...")
        for name in list(self.service_tasks.keys()):
            await self.disconnect_service(name)

# Instantiate Global State
state = OrchestratorGlobal()

# --- MCP Server Setup ---
mcp_server = Server("HR Agent Orchestrator")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """Lists all tools available from downstream services."""
    tools = []
    
    # Iterate through all configured services to ensure we have sessions
    for name in MCP_SERVICES.keys():
        session = await state.get_session(name)
        if not session:
            continue

        try:
            result = await session.list_tools()
            for t in result.tools:
                state.tool_map[t.name] = name
                clean_tool = Tool(
                    name=t.name,
                    description=t.description,
                    inputSchema=t.inputSchema
                )
                tools.append(clean_tool)
        except Exception as e:
            print(f"Error listing tools from {name}: {e}")
            await state.disconnect_service(name)
            
    return tools

@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    service_name = state.tool_map.get(name)

    # 1. Discovery: Ensure we know which service handles this tool
    if not service_name:
        await list_tools()
        service_name = state.tool_map.get(name)

    if not service_name:
        raise ValueError(f"Tool {name} not found.")

    print(f"🔧 Proxying tool {name} to {service_name}...")
    sys.stdout.flush()

    # 2. Execution Loop: Retry logic for lost connections
    for attempt in range(2):
        session = await state.get_session(service_name)
        
        # If session is dead, try to reconnect and restart loop
        if not session:
            await state.disconnect_service(service_name)
            continue

        try:
            # 3. TIMEOUT PROTECTION: Force a 25s limit so we can reply to Claude
            result = await asyncio.wait_for(
                session.call_tool(name, arguments or {}), 
                timeout=25.0 
            )

            # --- CRITICAL FIX START ---
            # 4. ROBUST CONTENT EXTRACTION (Fixes RAG Crashes)
            print(f"🔍 DEBUG: Raw Result Type from {name}: {type(result)}")
            sys.stdout.flush()

            texts = []
            
            # Iterate through content safely, handling various object types
            for c in result.content:
                clean_text = ""
                
                # Case A: Standard MCP TextContent Object
                if hasattr(c, 'text') and c.text:
                    clean_text = str(c.text) # Force string cast
                
                # Case B: Dictionary (JSON serialization issues)
                elif isinstance(c, dict) and 'text' in c:
                    clean_text = str(c['text'])
                
                # Case C: Fallback for other objects
                elif hasattr(c, 'type') and c.type == 'text':
                    # Try to extract text if it exists but wasn't caught above
                    clean_text = str(getattr(c, 'text', ''))

                # SANITIZE: Remove poison characters that break SSE streams and JSON
                if clean_text:
                    # Remove null bytes and carriage returns
                    clean_text = clean_text.replace("\x00", "").replace("\r", "")
                    # Replace smart quotes and other problematic Unicode
                    clean_text = clean_text.replace(""", '"').replace(""", '"')
                    clean_text = clean_text.replace("'", "'").replace("'", "'")
                    clean_text = clean_text.replace("–", "-").replace("—", "-")
                    # Ensure the text is valid for JSON (escape backslashes if raw)
                    if clean_text.strip():
                        texts.append(clean_text)

            # 5. EMPTY RESPONSE HANDLING
            if not texts:
                print("❌ No text found after processing RAG output.")
                return [TextContent(type="text", text="[Process finished, but no readable text content was returned by the tool.]")]

            # 6. VOLUME PROTECTION
            combined_text = "\n\n".join(texts)
            
            # Truncate to 4000 chars to prevent "Message Too Large" disconnects
            if len(combined_text) > 4000:
                print(f"✂️ Truncating output from {len(combined_text)} to 4000 chars")
                combined_text = combined_text[:4000] + "\n...[Output truncated for speed]..."
            
            # Final Debug Log
            print(f"🚀 Sending final payload ({len(combined_text)} chars) to Claude...")
            print(f"📦 First 200 chars of payload: {combined_text[:200]}")
            sys.stdout.flush()

            response_content = [TextContent(type="text", text=combined_text)]
            print(f"✅ Returning TextContent list with {len(response_content)} items")
            sys.stdout.flush()
            return response_content
            # --- CRITICAL FIX END ---

        except asyncio.TimeoutError:
            print(f"⏰ RAG Service timed out for tool {name}")
            return [TextContent(type="text", text="Error: The service took too long to retrieve the documents. Please try a more specific query.")]

        except Exception as e:
            print(f"💥 Error executing tool {name} (Attempt {attempt+1}): {e}")
            traceback.print_exc() # Print full stack trace to Docker logs
            
            # If it's a connection error, disconnect and let the loop retry
            if "connection" in str(e).lower() and attempt == 0:
                await state.disconnect_service(service_name)
                continue
                
            return [TextContent(type="text", text=f"System Error: {str(e)}")]

    raise RuntimeError(f"Failed to execute tool {name} after retries.")


# --- FastAPI App with Streamable HTTP ---

# Create the session manager for Streamable HTTP
session_manager = StreamableHTTPSessionManager(
    app=mcp_server,
    json_response=True,  # Use JSON responses for more reliability
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global session_manager
    # Connect to downstream services
    await state.connect_downstream()
    
    # Start the session manager
    async with session_manager.run():
        print("✅ Streamable HTTP Session Manager started!")
        sys.stdout.flush()
        yield
    
    # Shutdown
    await state.cleanup()

app = FastAPI(title="Orchestrator Service", lifespan=lifespan)

# Allow CORS - important: expose Mcp-Session-Id header
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=60.0)

# --- MCP Routes (For Claude Desktop via Streamable HTTP) ---

# ASGI handler for the MCP Streamable HTTP endpoint
async def handle_mcp_request(scope: Scope, receive: Receive, send: Send) -> None:
    """Handle all MCP Streamable HTTP requests."""
    await session_manager.handle_request(scope, receive, send)

# Mount the MCP handler on /mcp path
from starlette.routing import Route
from fastapi.responses import Response

class ASGIResponse(Response):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

@app.api_route("/mcp", methods=["GET", "POST", "DELETE", "OPTIONS"])
async def mcp_endpoint(request: Request):
    """Streamable HTTP MCP Endpoint - handles all MCP communication"""
    return ASGIResponse(handle_mcp_request)


# --- Chat Routes (For React Frontend) ---

class Message(BaseModel):
    role: str
    content: str
class ChatRequest(BaseModel):
    messages: List[Message]

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Existing chat endpoint for the React Frontend. 
    Refactored to use the global state.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")

    async def event_generator():
        # Build Tools List for OpenAI from the global tools
        mcp_tools = await list_tools() # Usage of our internal function
        
        openai_tools = []
        for tool in mcp_tools:
            # Clean schema
            clean_schema = tool.inputSchema.copy() if isinstance(tool.inputSchema, dict) else tool.inputSchema
            if "title" in clean_schema: del clean_schema["title"]
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": clean_schema
                }
            })

        conversation = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # System Prompt
        system_message = {
            "role": "system", 
            "content": (
                "You are the HR Assistant for this company. You must categorize the user's input and act accordingly:\n\n"
                "**CATEGORY 1: GREETINGS & SMALL TALK**\n"
                "- If the user says 'Hi', 'Hello', 'Who are you?', or 'Thanks', reply briefly and politely. Do not offer extra services unless asked.\n"
                "- You do NOT need tools for this.\n\n"
                "**CATEGORY 2: BUSINESS QUESTIONS (LEAVE, LOANS, POLICIES)**\n"
                "- You are an **INFORMATION RETRIEVAL BOT and an MCP who can do tasks**.\n"
                "- **Rule A (Context Verification):** Verify that tool output explicitly mentions the specific topic requested.\n"
                "- **Rule B:** Answer ONLY using information explicitly returned by the tools.\n"
                "- **Rule D:** If the tool output is empty or irrelevant, state you are unable to answer."
            )
        }
        if not conversation or conversation[0].get("role") != "system":
            conversation.insert(0, system_message)

        for _ in range(5): 
            # Check for Tool Calls or Final Answer
            stream = await openai_client.chat.completions.create(
                model="gpt-5-mini",
                messages=conversation,
                tools=openai_tools if openai_tools else None,
                tool_choice="auto" if openai_tools else None,
                stream=True
            )

            current_message_content = ""
            tool_calls = []

            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    current_message_content += delta.content
                    yield delta.content
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index is not None:
                            if len(tool_calls) <= tc.index:
                                tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                            if tc.id: tool_calls[tc.index]["id"] += tc.id
                            if tc.function.name: tool_calls[tc.index]["function"]["name"] += tc.function.name
                            if tc.function.arguments: tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

            conversation.append({
                "role": "assistant",
                "content": current_message_content if current_message_content else None,
                "tool_calls": [{"id": tc["id"], "type": "function", "function": tc["function"]} for tc in tool_calls] if tool_calls else None
            })

            if not tool_calls:
                break
            
            # Execute Tools using Global State
            for tc in tool_calls:
                func_name = tc["function"]["name"]
                func_args = tc["function"]["arguments"]
                call_id = tc["id"]
                
                try:
                    # Notify use (optional)
                    # yield f"\n\n*Using tool: {func_name}*\n\n" 
                    
                    arguments = json.loads(func_args)
                    # Use our own PROXY execution method
                    # Since we are inside the app, we can call mcp_server logic or just use state directly.
                    # Using state directly avoids the 'mcp_server' overhead for this internal call.
                    
                    # Resolve service
                    service_name = state.tool_map.get(func_name)
                    if service_name:
                        # Attempt to get a valid session (handles reconnects)
                        session = await state.get_session(service_name)
                        if session:
                            print(f"🔧 Chat calling Tool: {func_name} on {service_name}")
                            result = await session.call_tool(func_name, arguments)
                            print(f"🔍 DEBUG: Orchestrator received result from {func_name}: type={type(result)}")
                            print(f"🔍 DEBUG: Result content: {result.content}")
                            sys.stdout.flush()
                            text_results = [c.text for c in result.content if c.type == "text"]
                            result_content = "\n".join(text_results)
                        else:
                            result_content = f"Error: Service {service_name} unavailable for tool {func_name}."
                    else:
                        result_content = f"Error: Tool {func_name} not found."
                        
                except Exception as e:
                    result_content = f"Error executing tool {func_name}: {str(e)}"

                conversation.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": result_content
                })

    return StreamingResponse(event_generator(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
