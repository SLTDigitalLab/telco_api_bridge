#!/usr/bin/env python3
"""
MCP Client Bridge Server
Acts as a bridge between HTTP frontend and FastMCP server
This runs the MCP client that connects to FastMCP server and exposes HTTP endpoints
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import subprocess
import json
from datetime import datetime


class Product(BaseModel):
    product_id: str
    product_name: str
    product_category: str
    product_quantity: int
    created_at: str = ""
    updated_at: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "user"


class ChatResponse(BaseModel):
    response: str
    products: Optional[List[Product]] = None
    action_performed: Optional[str] = None
    success: bool = True


class MCPClientBridge:
    def __init__(self):
        self.mcp_process = None
        self.data_cache = []
        
    async def start_mcp_server(self):
        """Start the FastMCP server as a subprocess"""
        try:
            self.mcp_process = await asyncio.create_subprocess_exec(
                "uv", "run", "python", "fastmcp_server.py",
                cwd="D:\\SLT\\telco_api_bridge\\backend",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE
            )
            print("✅ FastMCP server started successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to start FastMCP server: {e}")
            return False
    
    async def send_mcp_query(self, query: str) -> str:
        """Send a query to the FastMCP server via MCP protocol"""
        try:
            if not self.mcp_process:
                await self.start_mcp_server()
            
            # For now, we'll use the process_query tool directly
            # In a real MCP implementation, this would use MCP protocol messages
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "process_query",
                    "arguments": {"query": query}
                }
            }
            
            request_json = json.dumps(mcp_request) + "\n"
            
            # Send request to MCP server
            if self.mcp_process and self.mcp_process.stdin:
                self.mcp_process.stdin.write(request_json.encode())
                await self.mcp_process.stdin.drain()
                
                # Read response
                response_line = await self.mcp_process.stdout.readline()
                if response_line:
                    response_data = json.loads(response_line.decode())
                    return response_data.get("result", {}).get("content", [{}])[0].get("text", "No response")
            
            return "❌ Failed to communicate with MCP server"
            
        except Exception as e:
            return f"❌ Error communicating with MCP server: {str(e)}"
    
    def load_products_from_json(self) -> List[Dict]:
        """Load products directly from JSON file for display"""
        try:
            with open("D:\\SLT\\telco_api_bridge\\backend\\data\\products.json", "r") as f:
                data = json.load(f)
                return data.get("products", [])
        except Exception as e:
            print(f"Error loading products: {e}")
            return []


# Initialize FastAPI app and MCP bridge
app = FastAPI(
    title="MCP Client Bridge",
    description="Bridge between HTTP frontend and FastMCP server",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

mcp_bridge = MCPClientBridge()


@app.on_event("startup")
async def startup_event():
    """Start MCP server on application startup"""
    await mcp_bridge.start_mcp_server()


@app.get("/")
async def root():
    return {
        "message": "MCP Client Bridge",
        "status": "Connected to FastMCP server",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "mcp_connected": mcp_bridge.mcp_process is not None}


@app.get("/api/v1/Products_DB", response_model=List[Product])
async def get_products(search: str = "", category: str = ""):
    """Get all products by querying MCP server"""
    try:
        # Load products directly from JSON for display
        products = mcp_bridge.load_products_from_json()
        
        # Filter if search or category specified
        if search:
            search_lower = search.lower()
            products = [p for p in products if (
                search_lower in p.get("product_name", "").lower() or
                search_lower in p.get("product_category", "").lower() or
                search_lower in p.get("product_id", "").lower()
            )]
        
        if category:
            category_lower = category.lower()
            products = [p for p in products if category_lower in p.get("product_category", "").lower()]
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat messages via MCP server"""
    try:
        # Send query to MCP server
        response_text = await mcp_bridge.send_mcp_query(request.message)
        
        # Load updated products after any operation
        products = mcp_bridge.load_products_from_json()
        
        # Determine action type
        message_lower = request.message.lower()
        if any(word in message_lower for word in ["add", "create", "new"]):
            action = "create"
        elif any(word in message_lower for word in ["update", "modify", "change"]):
            action = "update" 
        elif any(word in message_lower for word in ["delete", "remove"]):
            action = "delete"
        else:
            action = "search"
        
        return ChatResponse(
            response=response_text,
            products=products,
            action_performed=action,
            success="✅" in response_text
        )
        
    except Exception as e:
        return ChatResponse(
            response=f"❌ Error: {str(e)}",
            products=None,
            action_performed="error",
            success=False
        )


if __name__ == "__main__":
    import uvicorn
    print("🔗 Starting MCP Client Bridge Server")
    print("📡 This connects HTTP frontend to FastMCP server")
    print("🌐 Frontend: http://localhost:3000")
    print("🔗 Bridge API: http://localhost:8000")
    print("⚡ FastMCP Server: stdio transport")
    
    uvicorn.run(
        "mcp_client_bridge:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )