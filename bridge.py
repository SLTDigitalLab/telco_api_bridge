import sys
import os
import asyncio
import json
import httpx
import logging
import argparse
import uuid
import io

# Setup Logging
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bridge.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Fix Windows Unicode encoding issues - wrap stdin/stdout with UTF-8
if sys.platform == 'win32':
    # Reconfigure stdout/stdin to use UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')

async def bridge_loop(mcp_url):
    """
    Bridge for Streamable HTTP MCP transport.
    
    The Streamable HTTP transport works with simple HTTP POST requests:
    - Claude sends JSON-RPC requests via stdin
    - We POST them to /mcp endpoint and get JSON response
    - We send the response back to Claude via stdout
    
    Session management:
    - First request creates a session (server returns Mcp-Session-Id header)
    - Subsequent requests include Mcp-Session-Id header
    """
    logging.info(f"Starting Streamable HTTP bridge to {mcp_url}")
    
    session_id = None
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        loop = asyncio.get_running_loop()
        
        while True:
            try:
                # Read JSON-RPC request from Claude (stdin)
                line = await loop.run_in_executor(None, sys.stdin.readline)
                if not line:
                    logging.info("EOF on stdin, exiting")
                    break
                
                line = line.strip()
                if not line:
                    continue
                    
                logging.debug(f"Claude -> Server: {line[:150]}...")
                
                try:
                    request_data = json.loads(line)
                except json.JSONDecodeError as e:
                    logging.error(f"Invalid JSON from Claude: {e}")
                    continue
                
                # Build headers
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                }
                
                # Include session ID if we have one
                if session_id:
                    headers["Mcp-Session-Id"] = session_id
                
                # POST to MCP server
                try:
                    response = await client.post(
                        mcp_url,
                        json=request_data,
                        headers=headers
                    )
                    
                    # Capture session ID from response
                    if "Mcp-Session-Id" in response.headers:
                        new_session_id = response.headers["Mcp-Session-Id"]
                        if session_id != new_session_id:
                            session_id = new_session_id
                            logging.info(f"Session established: {session_id}")
                    
                    # Log response status
                    logging.debug(f"Response status: {response.status_code}")
                    
                    # Handle response
                    if response.status_code == 200:
                        response_text = response.text.strip()
                        if response_text:
                            logging.debug(f"Server -> Claude ({len(response_text)} chars): {response_text[:150]}...")
                            sys.stdout.write(response_text + "\n")
                            sys.stdout.flush()
                            logging.info("Message forwarded to Claude successfully")
                    elif response.status_code == 202:
                        # Accepted - notification sent, no response body expected
                        logging.debug("Request accepted (202)")
                    else:
                        logging.error(f"Server error: {response.status_code} - {response.text}")
                        # Send error response to Claude
                        error_response = json.dumps({
                            "jsonrpc": "2.0",
                            "id": request_data.get("id"),
                            "error": {"code": -32603, "message": f"Server error: {response.status_code}"}
                        })
                        sys.stdout.write(error_response + "\n")
                        sys.stdout.flush()
                        
                except httpx.HTTPError as e:
                    logging.error(f"HTTP error: {e}")
                    # Send error response to Claude
                    error_response = json.dumps({
                        "jsonrpc": "2.0",
                        "id": request_data.get("id"),
                        "error": {"code": -32603, "message": str(e)}
                    })
                    sys.stdout.write(error_response + "\n")
                    sys.stdout.flush()
                    
            except Exception as e:
                logging.error(f"Error in bridge loop: {e}", exc_info=True)
                continue

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="The MCP URL (e.g., http://localhost:8005/mcp)")
    args = parser.parse_args()

    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(bridge_loop(args.url))
    except KeyboardInterrupt:
        pass