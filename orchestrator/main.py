"""
HR Agent Orchestrator - StreamableHTTP Transport

This orchestrator connects to downstream MCP services (Leave, Loan, Policy)
and exposes their tools via StreamableHTTP to Claude Desktop and other clients.

Architecture:
  Claude Desktop → StreamableHTTP /mcp → Orchestrator → SSE → MCP Services (Docker)
  React Frontend → HTTP /chat → Orchestrator → SSE → MCP Services (Docker)
"""

import os
import uvicorn
import json
import asyncio
import sys
import traceback
import contextlib
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

from urllib.parse import urlparse
from contextlib import AsyncExitStack, asynccontextmanager
from typing import List, Dict, Any, Optional, Callable

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.routing import Mount
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logging.getLogger("mcp").setLevel(logging.DEBUG)
logging.getLogger("uvicorn").setLevel(logging.INFO)

# MCP Imports
from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from openai import AsyncOpenAI

# --- Configuration ---
MCP_SERVICES = {
    "leave": os.getenv("LEAVE_SERVICE_URL", "http://localhost:8000/sse"),
    "loan": os.getenv("LOAN_SERVICE_URL", "http://localhost:8001/sse"),
    "policy": os.getenv("POLICY_SERVICE_URL", "http://localhost:8002/sse"),
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- FastMCP Server ---
mcp = FastMCP("HR Agent Orchestrator")

# --- Global State & Connection Manager ---
class OrchestratorState:
    def __init__(self):
        self.service_tasks: Dict[str, asyncio.Task] = {}
        self.service_stop_events: Dict[str, asyncio.Event] = {}
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map: Dict[str, str] = {}  # tool_name -> service_name
        self.registered_tools: set = set()  # Track registered tool names

    async def _manage_service_connection(self, name: str, url: str, stop_event: asyncio.Event, ready_future: asyncio.Future):
        """Background task to maintain connection context."""
        async with AsyncExitStack() as stack:
            try:
                print(f"🔌 Connecting to {name} at {url}...")
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
                print(f"✅ Connected to {name}")
                sys.stdout.flush()
                
                if not ready_future.done():
                    ready_future.set_result(True)
                
                # Keep alive until stop requested
                await stop_event.wait()
                print(f"Stopping connection task for {name}")

            except Exception as e:
                print(f"⚠️ Connection error for {name}: {e}")
                sys.stdout.flush()
                if not ready_future.done():
                    ready_future.set_exception(e)
            finally:
                if name in self.sessions:
                    del self.sessions[name]

    async def connect_service(self, name: str, url: str) -> Optional[ClientSession]:
        """Connect to a single service."""
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
            print(f"⚠️ Failed to connect to {name}: {e}")
            await self.disconnect_service(name)
            return None

    async def disconnect_service(self, name: str):
        """Disconnect from a service."""
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
                print(f"Error during disconnect of {name}: {e}")
        
        if name in self.sessions:
            del self.sessions[name]

    async def get_session(self, name: str) -> Optional[ClientSession]:
        """Get existing session or reconnect."""
        if name in self.sessions:
            return self.sessions[name]
        
        url = MCP_SERVICES.get(name)
        if url:
            return await self.connect_service(name, url)
        return None

    async def connect_all(self):
        """Initial connection to all services."""
        print("Connecting to all downstream services...")
        sys.stdout.flush()
        for name, url in MCP_SERVICES.items():
            await self.connect_service(name, url)

    async def cleanup(self):
        """Cleanup all connections."""
        print("Closing all downstream connections...")
        for name in list(self.service_tasks.keys()):
            await self.disconnect_service(name)

# Instantiate global state
state = OrchestratorState()


# --- Static MCP Tools ---
# Instead of dynamic registration (which has schema issues), 
# we provide meta-tools that work with any downstream tool

@mcp.tool()
async def list_available_tools() -> str:
    """List all available HR tools from downstream services."""
    tools = []
    for service_name in MCP_SERVICES.keys():
        session = await state.get_session(service_name)
        if not session:
            continue
        try:
            result = await session.list_tools()
            for t in result.tools:
                state.tool_map[t.name] = service_name
                tools.append({
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema
                })
        except Exception as e:
            print(f"Error listing tools from {service_name}: {e}")
    
    return json.dumps(tools, indent=2)


@mcp.tool()
async def execute_hr_tool(tool_name: str, arguments_json: str = "{}") -> str:
    """
    Execute any HR tool by name with JSON arguments.
    
    Use list_available_tools first to see what's available.
    
    Args:
        tool_name: The name of the tool to execute (e.g., 'search_hr_policies', 'get_leave_balance')
        arguments_json: JSON string of arguments (e.g., '{"query": "maternity leave"}' or '{"employee_id": "E001"}')
    """
    try:
        arguments = json.loads(arguments_json) if arguments_json else {}
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON arguments: {e}"
    
    return await execute_tool(tool_name, arguments)


async def register_downstream_tools():
    """
    Pre-populate tool_map by connecting to downstream services.
    Tools are exposed through execute_hr_tool proxy.
    """
    print("📋 Discovering downstream tools...")
    
    for service_name in MCP_SERVICES.keys():
        session = await state.get_session(service_name)
        if not session:
            print(f"⚠️ Skipping {service_name} - not connected")
            continue
        
        try:
            result = await session.list_tools()
            for tool in result.tools:
                state.tool_map[tool.name] = service_name
                print(f"    ✅ Found: {tool.name}")
        except Exception as e:
            print(f"⚠️ Error listing tools from {service_name}: {e}")
    
    print(f"📋 Total tools available: {len(state.tool_map)}")


async def execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute a tool on the appropriate downstream service."""
    service_name = state.tool_map.get(tool_name)
    
    if not service_name:
        # Try to rediscover
        await register_downstream_tools()
        service_name = state.tool_map.get(tool_name)
    
    if not service_name:
        raise ValueError(f"Tool {tool_name} not found")
    
    print(f"🔧 Executing {tool_name} on {service_name}...")
    sys.stdout.flush()
    
    for attempt in range(2):
        session = await state.get_session(service_name)
        
        if not session:
            await state.disconnect_service(service_name)
            continue
        
        try:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments or {}),
                timeout=25.0
            )
            
            # Extract text from result
            texts = []
            for c in result.content:
                if hasattr(c, 'text') and c.text:
                    texts.append(str(c.text))
                elif isinstance(c, dict) and 'text' in c:
                    texts.append(str(c['text']))
            
            if not texts:
                return "[No content returned by tool]"
            
            combined = "\n\n".join(texts)
            
            # Truncate if too long
            if len(combined) > 4000:
                combined = combined[:4000] + "\n...[truncated]..."
            
            print(f"✅ {tool_name} returned {len(combined)} chars")
            return combined
            
        except asyncio.TimeoutError:
            return f"Error: {tool_name} timed out"
        except Exception as e:
            print(f"💥 Error executing {tool_name}: {e}")
            if "connection" in str(e).lower() and attempt == 0:
                await state.disconnect_service(service_name)
                continue
            return f"Error: {str(e)}"
    
    return f"Error: Failed to execute {tool_name}"


# --- FastAPI App ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - manage connections and MCP session manager."""
    # Connect to downstream services
    await state.connect_all()
    
    # Register tools from downstream services
    await register_downstream_tools()
    
    # Start FastMCP session manager
    async with mcp.session_manager.run():
        print("✅ Orchestrator started with StreamableHTTP transport!")
        print(f"📍 MCP endpoint: http://localhost:8005/mcp")
        print(f"📍 Chat endpoint: http://localhost:8005/chat")
        sys.stdout.flush()
        yield
    
    # Cleanup
    await state.cleanup()


# Create FastAPI app
app = FastAPI(title="HR Agent Orchestrator", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)

# Mount StreamableHTTP app at /mcp
app.mount("/mcp", mcp.streamable_http_app())

# Also mount SSE for backwards compatibility (optional)
# app.mount("/sse", mcp.sse_app())


# --- Chat Endpoint for React Frontend ---
openai_client = None

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]


async def get_all_tools() -> list[Tool]:
    """Get all available tools from downstream services."""
    tools = []
    for name in MCP_SERVICES.keys():
        session = await state.get_session(name)
        if not session:
            continue
        try:
            result = await session.list_tools()
            for t in result.tools:
                state.tool_map[t.name] = name
                tools.append(Tool(
                    name=t.name,
                    description=t.description,
                    inputSchema=t.inputSchema
                ))
        except Exception as e:
            print(f"Error listing tools from {name}: {e}")
    return tools


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """Chat endpoint for React Frontend."""
    global openai_client
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set")
    
    if openai_client is None:
        openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=60.0)

    async def event_generator():
        # Get tools for OpenAI
        mcp_tools = await get_all_tools()
        
        openai_tools = []
        for tool in mcp_tools:
            clean_schema = tool.inputSchema.copy() if isinstance(tool.inputSchema, dict) else tool.inputSchema
            if "title" in clean_schema:
                del clean_schema["title"]
            
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": clean_schema
                }
            })

        conversation = [{"role": m.role, "content": m.content} for m in request.messages]
        
        # System prompt
        system_message = {
            "role": "system",
            "content": (
                "You are the HR Assistant for this company. You must categorize the user's input and act accordingly:\n\n"
                "**CATEGORY 1: GREETINGS & SMALL TALK**\n"
                "- If the user says 'Hi', 'Hello', 'Who are you?', or 'Thanks', reply briefly and politely.\n\n"
                "**CATEGORY 2: BUSINESS QUESTIONS (LEAVE, LOANS, POLICIES)**\n"
                "- You are an INFORMATION RETRIEVAL BOT and an MCP who can do tasks.\n"
                "- Answer ONLY using information returned by the tools.\n"
                "- If the tool output is empty or irrelevant, state you are unable to answer."
            )
        }
        if not conversation or conversation[0].get("role") != "system":
            conversation.insert(0, system_message)

        for _ in range(5):
            stream = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
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
                        if tc.index >= len(tool_calls):
                            tool_calls.append({"id": "", "function": {"name": "", "arguments": ""}})
                        if tc.id:
                            tool_calls[tc.index]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls[tc.index]["function"]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls[tc.index]["function"]["arguments"] += tc.function.arguments

            if not tool_calls:
                break

            # Add assistant message with tool calls
            conversation.append({
                "role": "assistant",
                "content": current_message_content or None,
                "tool_calls": [
                    {"id": tc["id"], "type": "function", "function": tc["function"]}
                    for tc in tool_calls
                ]
            })

            # Execute tool calls
            for tc in tool_calls:
                call_id = tc["id"]
                func_name = tc["function"]["name"]
                try:
                    arguments = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    arguments = {}

                try:
                    result_content = await execute_tool(func_name, arguments)
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
