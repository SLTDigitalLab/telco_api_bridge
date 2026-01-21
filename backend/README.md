# SLT MCP Server

A standalone Model Context Protocol (MCP) server for product database operations with natural language query support.

## Overview

This MCP server provides CRUD operations for a product database through natural language queries and direct tool calls. It runs independently and can be connected to by any MCP client (Claude Desktop, web interfaces, custom clients, etc.).

## Architecture

- **Standalone MCP Server**: Runs independently with stdio transport
- **JSON Data Storage**: Simple file-based storage for product data
- **Natural Language Processing**: Regex-based query understanding
- **Tool-based Interface**: Exposes database operations as MCP tools

## Features

- Natural language query processing
- Product CRUD operations (Create, Read, Update, Delete)
- Product search functionality
- JSON-based data persistence
- MCP protocol compliance

## Installation

```bash
# Install dependencies
uv sync

# Or install in development mode
uv sync --dev
```

## Usage

### Starting the MCP Server

```bash
# Using UV
uv run python run_server.py

# Or directly
uv run python mcp_server_standalone.py
```

### Testing with MCP Client

```bash
# Run the test client
uv run python mcp_client_test.py
```

### Example Queries

- "show all products"
- "get product SLT001"
- "add product PROD999 TestProduct TestCategory 10"
- "update product SLT001 quantity to 600"
- "delete product PROD999"
- "search for fiber products"

## Data Structure

Products are stored in `data/products.json` with the following structure:

```json
{
  "products": [
    {
      "product_id": "SLT001",
      "product_name": "Fiber Broadband 100Mbps",
      "product_category": "Internet Services",
      "product_quantity": 500
    }
  ]
}
```

## Available Tools

1. **process_query** - Process natural language queries
2. **get_all_products** - Get all products
3. **get_product** - Get specific product by ID
4. **add_product** - Add new product
5. **update_product** - Update existing product
6. **delete_product** - Delete product by ID
7. **search_products** - Search products by term

## Project Structure

```
backend/
├── mcp_server_standalone.py  # Main MCP server
├── nl_processor.py           # Natural language processing
├── data_manager.py          # JSON data operations
├── mcp_client_test.py       # Test client
├── run_server.py            # Server startup script
└── data/
    └── products.json        # Product data storage
```