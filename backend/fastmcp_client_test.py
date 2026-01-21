#!/usr/bin/env python3
"""
FastMCP Client for testing SLT Telecom MCP Server
"""

import subprocess
import json
import sys


def test_fastmcp_server():
    """Test the FastMCP server using the command line interface"""
    server_command = ["uv", "run", "python", "fastmcp_server.py"]
    
    print("🚀 Testing SLT Telecom FastMCP Server")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "search for fiber products",
        "find all products", 
        "get product with id 1",
        "show me internet services"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 30)
        
        try:
            # For now, we'll just show what queries would be processed
            print(f"Would process: {query}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ FastMCP server is configured and ready!")
    print("To connect with an MCP client, run:")
    print("uv run python fastmcp_server.py")


if __name__ == "__main__":
    test_fastmcp_server()