"""
Bridge for Claude Desktop -> Orchestrator StreamableHTTP connection.

This script runs as a subprocess of Claude Desktop (stdio transport)
and forwards MCP requests to the orchestrator's StreamableHTTP endpoint.
"""
import sys
import os
import asyncio
import json
import logging
import argparse
import io

# Setup Logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bridge.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Fix Windows Unicode encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

import httpx

class StreamableHTTPBridge:
    """Bridge between stdio (Claude Desktop) and StreamableHTTP (Orchestrator)."""
    
    def __init__(self, url: str):
        self.url = url
        self.session_id = None
        self.client = httpx.AsyncClient(timeout=120.0)
    
    async def send_request(self, request: dict) -> dict:
        """Send a JSON-RPC request to the orchestrator's StreamableHTTP endpoint."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        
        logging.debug(f"Sending to orchestrator: {json.dumps(request)[:500]}...")
        
        response = await self.client.post(self.url, json=request, headers=headers)
        
        # Get session ID from response
        if "mcp-session-id" in response.headers:
            self.session_id = response.headers["mcp-session-id"]
            logging.debug(f"Got session ID: {self.session_id}")
        
        # Parse SSE response
        text = response.text
        logging.debug(f"Raw response: {text[:500]}...")
        
        # Extract JSON from SSE format (event: message\ndata: {...})
        result = None
        for line in text.split('\n'):
            if line.startswith('data: '):
                try:
                    result = json.loads(line[6:])
                    break
                except json.JSONDecodeError:
                    continue
        
        if result is None:
            # Try parsing as plain JSON
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                logging.error(f"Failed to parse response: {text[:200]}")
                raise ValueError("Invalid response from orchestrator")
        
        return result
    
    async def close(self):
        await self.client.aclose()


async def stdio_loop(bridge: StreamableHTTPBridge):
    """Main stdio communication loop."""
    logging.info(f"Starting StreamableHTTP bridge to {bridge.url}")
    
    loop = asyncio.get_running_loop()
    
    while True:
        try:
            # Read line from stdin
            line = await loop.run_in_executor(None, sys.stdin.readline)
            
            if not line:
                logging.info("EOF on stdin, exiting")
                break
            
            line = line.strip()
            if not line:
                continue
            
            logging.debug(f"Received from Claude: {line[:200]}...")
            
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON from Claude: {e}")
                continue
            
            method = request.get("method", "")
            
            # Skip notifications (no response needed)
            if method.startswith("notifications/"):
                logging.debug(f"Skipping notification: {method}")
                continue
            
            # Forward to orchestrator
            try:
                response = await bridge.send_request(request)
                response_str = json.dumps(response)
                logging.debug(f"Sending to Claude: {response_str[:200]}...")
                sys.stdout.write(response_str + "\n")
                sys.stdout.flush()
            except Exception as e:
                logging.error(f"Error forwarding request: {e}", exc_info=True)
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32603, "message": str(e)}
                }
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()
                
        except Exception as e:
            logging.error(f"Error in stdio loop: {e}", exc_info=True)
            continue
    
    await bridge.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The StreamableHTTP URL (e.g., http://localhost:8005/mcp/mcp)")
    args = parser.parse_args()

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    bridge = StreamableHTTPBridge(args.url)
    
    try:
        asyncio.run(stdio_loop(bridge))
    except KeyboardInterrupt:
        logging.info("Bridge terminated by user")