#!/usr/bin/env python3
"""
SLT Telecom MCP Server - Unified Architecture
Single server that handles both MCP protocol and HTTP for frontend
This is the correct approach for the standalone MCP server
"""

from fastmcp import FastMCP
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
import uvicorn
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


class QueryType(Enum):
    SEARCH = "search"
    GET = "get" 
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    UNKNOWN = "unknown"


@dataclass
class QueryParams:
    query_type: QueryType
    product_id: Optional[str] = None
    search_term: Optional[str] = None
    product_data: Optional[Dict[str, Any]] = None


# HTTP API Models
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


class JSONDataManager:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """Ensure the data file exists with initial SLT data"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "products": [
                    {
                        "id": "1",
                        "name": "SLT Fiber 100Mbps",
                        "category": "Internet Services",
                        "description": "High-speed fiber internet connection with 100Mbps download speed",
                        "features": ["100Mbps Download", "20Mbps Upload", "Unlimited Data", "WiFi Router Included"],
                        "product_id": "SLT001",
                        "product_name": "SLT Fiber 100Mbps", 
                        "product_category": "Internet Services",
                        "product_quantity": 500,
                        "created_at": "2024-01-15T10:00:00Z"
                    },
                    {
                        "id": "2", 
                        "name": "SLT PEO TV Premium",
                        "category": "Digital TV",
                        "description": "Premium IPTV service with local and international channels",
                        "features": ["150+ Channels", "HD Quality", "Catch-up TV", "Mobile App Access"],
                        "product_id": "SLT002",
                        "product_name": "SLT PEO TV Premium",
                        "product_category": "Digital TV", 
                        "product_quantity": 300,
                        "created_at": "2024-01-15T10:00:00Z"
                    },
                    {
                        "id": "3",
                        "name": "SLT Mobitel 4G SIM",
                        "category": "Mobile Services",
                        "description": "4G mobile SIM card with voice and data services",
                        "features": ["4G Network", "Voice Calls", "SMS", "Data Plans"],
                        "product_id": "SLT003",
                        "product_name": "SLT Mobitel 4G SIM",
                        "product_category": "Mobile Services",
                        "product_quantity": 1000,
                        "created_at": "2024-01-15T10:00:00Z"
                    }
                ]
            }
            with open(self.data_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def load_data(self) -> Dict:
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"products": []}
    
    def save_data(self, data: Dict):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_all_products(self) -> List[Dict]:
        data = self.load_data()
        return data.get("products", [])
    
    def search_products(self, search_term: str = "") -> List[Dict]:
        products = self.get_all_products()
        
        if not search_term:
            return products
        
        search_term = search_term.lower()
        results = []
        for product in products:
            if (search_term in product.get("name", "").lower() or 
                search_term in product.get("product_name", "").lower() or
                search_term in product.get("category", "").lower() or
                search_term in product.get("product_category", "").lower() or
                search_term in product.get("description", "").lower()):
                results.append(product)
        
        return results
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        products = self.get_all_products()
        for product in products:
            if product.get("product_id") == product_id:
                return product
        return None
    
    def create_product(self, product_data: Dict) -> Dict:
        data = self.load_data()
        products = data.get("products", [])
        
        # Generate new ID if not provided
        if "product_id" not in product_data:
            existing_nums = []
            for p in products:
                if p.get("product_id", "").startswith("SLT"):
                    try:
                        num = int(p["product_id"][3:])
                        existing_nums.append(num)
                    except ValueError:
                        pass
            
            next_num = max(existing_nums) + 1 if existing_nums else 1
            product_data["product_id"] = f"SLT{next_num:03d}"
        
        # Set required fields with defaults if not provided
        product_data.setdefault("product_name", "New Product")
        product_data.setdefault("product_category", "General")  
        product_data.setdefault("product_quantity", 0)
        product_data["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        products.append(product_data)
        data["products"] = products
        self.save_data(data)
        
        return product_data
    
    def update_product(self, product_id: str, product_data: Dict) -> Optional[Dict]:
        data = self.load_data()
        products = data.get("products", [])
        
        for i, product in enumerate(products):
            if product.get("product_id") == product_id:
                # Update only provided fields
                for key, value in product_data.items():
                    if value is not None:
                        product[key] = value
                
                product["updated_at"] = datetime.utcnow().isoformat() + "Z"
                products[i] = product
                data["products"] = products
                self.save_data(data)
                return product
        
        return None
    
    def delete_product(self, product_id: str) -> bool:
        data = self.load_data()
        products = data.get("products", [])
        
        for i, product in enumerate(products):
            if product.get("product_id") == product_id:
                products.pop(i)
                data["products"] = products
                self.save_data(data)
                return True
        
        return False


class NaturalLanguageProcessor:
    def extract_query_params(self, query: str) -> QueryParams:
        """Extract query parameters from natural language with specific field extraction"""
        query_lower = query.lower()
        query_type = QueryType.UNKNOWN
        
        # Determine query type with better priority
        if any(word in query_lower for word in ["create", "add", "new", "insert", "make"]):
            query_type = QueryType.CREATE
        elif any(word in query_lower for word in ["update", "modify", "edit", "change", "set"]):
            query_type = QueryType.UPDATE  
        elif any(word in query_lower for word in ["delete", "remove", "drop", "eliminate"]):
            query_type = QueryType.DELETE
        elif any(word in query_lower for word in ["get", "show", "display"]) and any(word in query_lower for word in ["slt", "id"]) or "product " in query_lower:
            query_type = QueryType.GET
        elif any(word in query_lower for word in ["find", "search", "look", "list", "show", "display", "all"]):
            query_type = QueryType.SEARCH
        
        # Extract parameters
        product_id = None
        search_term = None
        product_data = {}
        
        # Extract product ID if present  
        import re
        
        # Look for SLT001 format or just numbers
        slt_match = re.search(r'slt(\d{3})', query_lower)
        if slt_match:
            product_id = f"SLT{slt_match.group(1)}"
        else:
            id_match = re.search(r'\bid\s*[:\s]*([\'"]?)(slt\d+|SLT\d+|\d+)\1', query_lower)
            if id_match:
                extracted_id = id_match.group(2).upper()
                if not extracted_id.startswith('SLT'):
                    extracted_id = f"SLT{extracted_id.zfill(3)}"
                product_id = extracted_id
        
        # Extract specific product fields for CREATE/UPDATE operations
        if query_type in [QueryType.CREATE, QueryType.UPDATE]:
            # Extract product_name
            name_match = re.search(r'(?:name|product_name)[:=]\s*[\'"]([^\'"]+)[\'"]', query_lower)
            if name_match:
                product_data['product_name'] = name_match.group(1)
            
            # Extract product_category  
            category_match = re.search(r'(?:category|product_category)[:=]\s*[\'"]([^\'"]+)[\'"]', query_lower)
            if category_match:
                product_data['product_category'] = category_match.group(1)
            
            # Extract product_quantity
            quantity_match = re.search(r'(?:quantity|product_quantity|amount)[:=]?\s*(\d+)', query_lower)
            if quantity_match:
                product_data['product_quantity'] = int(quantity_match.group(1))
        
        # Extract search terms
        if query_type == QueryType.SEARCH:
            stop_words = {"find", "search", "look", "for", "show", "me", "list", "products", "items", "services", "all", "the", "and", "or"}
            words = query_lower.split()
            search_words = [w for w in words if w not in stop_words and len(w) > 2 and not w.startswith('slt')]
            if search_words:
                search_term = " ".join(search_words)
        
        return QueryParams(
            query_type=query_type,
            product_id=product_id,
            search_term=search_term,
            product_data=product_data if product_data else None
        )


# Initialize components
data_manager = JSONDataManager("data/products.json")
nl_processor = NaturalLanguageProcessor()

# Initialize FastMCP
mcp = FastMCP("SLT Telecom MCP Server")


@mcp.tool()
def process_query(query: str) -> str:
    """Process natural language queries for product database operations - Main MCP Tool"""
    params = nl_processor.extract_query_params(query)
    
    try:
        if params.query_type == QueryType.CREATE:
            # Extract product details from query
            if "fiber" in query.lower() or "internet" in query.lower():
                product_data = {
                    "name": "Fiber Broadband 300Mbps",
                    "category": "Internet Services",
                    "product_quantity": 300,
                    "description": "High-speed fiber internet connection",
                    "features": ["300Mbps Download", "50Mbps Upload", "Unlimited Data"]
                }
            elif "tv" in query.lower() or "peotv" in query.lower():
                product_data = {
                    "name": "PeoTV Sports Premium", 
                    "category": "Digital TV",
                    "product_quantity": 250,
                    "description": "Premium TV package with sports channels",
                    "features": ["200+ Channels", "Sports Package", "HD Quality"]
                }
            elif "mobile" in query.lower() or "sim" in query.lower():
                product_data = {
                    "name": "SLT Mobitel 5G Premium",
                    "category": "Mobile Services", 
                    "product_quantity": 800,
                    "description": "5G mobile service with unlimited data",
                    "features": ["5G Network", "Unlimited Data", "Voice Calls"]
                }
            else:
                return "❌ Please specify product type (fiber/internet, tv/peotv, mobile/sim)"
            
            result = data_manager.create_product(product_data)
            return f"✅ Successfully created: {result['name']} (ID: {result['product_id']})"
            
        elif params.query_type == QueryType.UPDATE:
            if not params.product_id:
                return "❌ Please specify product ID to update (e.g., 'Update product 1')"
            
            # Extract quantity updates
            import re
            qty_match = re.search(r'quantity.*?(\d+)|to\s+(\d+)', query.lower())
            if qty_match:
                new_qty = int(qty_match.group(1) or qty_match.group(2))
                product_data = {"price": new_qty, "product_quantity": new_qty}
                result = data_manager.update_product(params.product_id, product_data)
                if result:
                    return f"✅ Updated product {params.product_id}: quantity set to {new_qty}"
                else:
                    return f"❌ Product {params.product_id} not found"
            
            return f"❌ Please specify what to update for product {params.product_id}"
        
        elif params.query_type == QueryType.DELETE:
            if not params.product_id:
                return "❌ Please specify product ID to delete (e.g., 'Delete product 1')"
            
            success = data_manager.delete_product(params.product_id)
            if success:
                return f"✅ Successfully deleted product {params.product_id}"
            else:
                return f"❌ Product {params.product_id} not found"
        
        elif params.query_type == QueryType.SEARCH:
            results = data_manager.search_products(params.search_term or "")
            if results:
                return f"📋 Found {len(results)} products:\n" + "\n".join([
                    f"- {p.get('name', p.get('product_name', 'Unknown'))} ({p.get('product_id', p.get('id', 'Unknown'))}) - {p.get('category', p.get('product_category', 'N/A'))}"
                    for p in results[:5]  # Limit to first 5 for readability
                ]) + (f"\n...and {len(results)-5} more" if len(results) > 5 else "")
            else:
                return "❌ No products found matching your search criteria."
                
        elif params.query_type == QueryType.GET:
            if not params.product_id:
                return "❌ Please specify a product ID to retrieve details."
            
            product = data_manager.get_product(params.product_id)
            if product:
                return f"📋 Product Details:\n" + json.dumps(product, indent=2)
            else:
                return f"❌ Product with ID '{params.product_id}' not found."
                
        else:
            return """
🤖 I can help you with product operations:

**CREATE**: "Add a new fiber product", "Create mobile service", "Add TV package"
**READ**: "Show all products", "Find fiber products", "Get product 1"
**UPDATE**: "Update product 1 quantity to 500", "Change product 2 quantity to 300" 
**DELETE**: "Delete product 3", "Remove product 5"

Try any of these commands!
            """.strip()
            
    except Exception as e:
        return f"❌ Error processing query: {str(e)}"


# Initialize FastAPI for HTTP endpoints (frontend compatibility)
app = FastAPI(
    title="SLT Telecom MCP Server",
    description="Unified MCP Server with HTTP endpoints for frontend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "SLT Telecom MCP Server",
        "version": "1.0.0",
        "status": "running",
        "mcp_tools": ["process_query"],
        "http_endpoints": {
            "products": "/api/v1/Products_DB",
            "chat": "/api/v1/chat"
        }
    }


@app.get("/api/v1/Products_DB", response_model=List[Product])
async def get_products(search: str = "", category: str = ""):
    """Get all products - HTTP endpoint for frontend"""
    try:
        products = data_manager.search_products(search)
        if category:
            products = [p for p in products if category.lower() in p.get("product_category", "").lower()]
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat messages via direct natural language processing"""
    try:
        # Process the query directly using our NL processor and data manager
        params = nl_processor.extract_query_params(request.message)
        query = request.message.lower()
        
        if params.query_type == QueryType.CREATE:
            # Check if specific parameters are provided
            if params.product_data:
                # Use provided parameters
                result = data_manager.create_product(params.product_data)
                response_text = f"✅ Successfully created: {result['product_name']} (ID: {result['product_id']}, Category: {result['product_category']}, Quantity: {result['product_quantity']})"
            else:
                # Auto-create based on keywords (fallback)
                if "fiber" in query or "internet" in query:
                    product_data = {
                        "product_name": "Fiber Broadband 300Mbps",
                        "product_category": "Internet Services",
                        "product_quantity": 100
                    }
                elif "tv" in query or "peotv" in query:
                    product_data = {
                        "product_name": "PeoTV Sports Premium", 
                        "product_category": "Digital TV",
                        "product_quantity": 200
                    }
                elif "mobile" in query or "sim" in query:
                    product_data = {
                        "product_name": "SLT Mobitel 5G Premium",
                        "product_category": "Mobile Services", 
                        "product_quantity": 500
                    }
                else:
                    return ChatResponse(
                        response="""❌ Please specify product details. Examples:
                        
**Specific CREATE**: "Create product_name:'WiFi Router' product_category:'Hardware' product_quantity:50"
**OR Auto CREATE**: "Add fiber product" / "Create mobile service" / "Add TV package" """,
                        products=None,
                        action_performed="create_help",
                        success=False
                    )
                
                result = data_manager.create_product(product_data)
                response_text = f"✅ Successfully created: {result['product_name']} (ID: {result['product_id']})"
            action = "create"
            
        elif params.query_type == QueryType.UPDATE:
            if not params.product_id:
                return ChatResponse(
                    response="""❌ Please specify product ID to update. Examples:
                    
**Specific UPDATE**: "Update SLT001 product_name:'New Name' product_quantity:800"
**OR Simple UPDATE**: "Update product SLT002 quantity 500" """,
                    products=None,
                    action_performed="update_help",
                    success=False
                )
            
            # Check if specific parameters are provided
            if params.product_data:
                result = data_manager.update_product(params.product_id, params.product_data)
                if result:
                    updated_fields = ", ".join([f"{k}: {v}" for k, v in params.product_data.items()])
                    response_text = f"✅ Updated product {params.product_id}: {updated_fields}"
                    action = "update"
                else:
                    response_text = f"❌ Product {params.product_id} not found"
                    action = "update_error"
            else:
                # Extract simple quantity updates (fallback)
                import re
                qty_match = re.search(r'quantity.*?(\d+)|to\s+(\d+)', query)
                if qty_match:
                    new_qty = int(qty_match.group(1) or qty_match.group(2))
                    product_data = {"product_quantity": new_qty}
                    result = data_manager.update_product(params.product_id, product_data)
                    if result:
                        response_text = f"✅ Updated product {params.product_id}: quantity set to {new_qty}"
                        action = "update"
                    else:
                        response_text = f"❌ Product {params.product_id} not found"
                        action = "update_error"
                else:
                    response_text = f"❌ Please specify what to update for product {params.product_id}"
                    action = "update_help"
        
        elif params.query_type == QueryType.DELETE:
            if not params.product_id:
                return ChatResponse(
                    response="""❌ Please specify product ID to delete. Examples:
                    
**DELETE by ID**: "Delete SLT003" / "Remove product SLT005" """,
                    products=None,
                    action_performed="delete_help",
                    success=False
                )
            
            # Get product details before deletion
            product_to_delete = data_manager.get_product(params.product_id)
            success = data_manager.delete_product(params.product_id)
            if success:
                response_text = f"✅ Successfully deleted: {product_to_delete['product_name']} (ID: {params.product_id})"
                action = "delete"
            else:
                response_text = f"❌ Product {params.product_id} not found"
                action = "delete_error"
        
        elif params.query_type == QueryType.SEARCH:
            results = data_manager.search_products(params.search_term or "")
            if results:
                response_text = f"📋 Found {len(results)} products:\n" + "\n".join([
                    f"- {p.get('name', p.get('product_name', 'Unknown'))} ({p.get('product_id', p.get('id', 'Unknown'))}) - {p.get('category', p.get('product_category', 'N/A'))}"
                    for p in results[:5]  # Limit to first 5 for readability
                ]) + (f"\n...and {len(results)-5} more" if len(results) > 5 else "")
                action = "search"
            else:
                response_text = "❌ No products found matching your search criteria."
                action = "search_empty"
                
        elif params.query_type == QueryType.GET:
            if not params.product_id:
                return ChatResponse(
                    response="❌ Please specify a product ID to retrieve details.",
                    products=None,
                    action_performed="get_help",
                    success=False
                )
            
            product = data_manager.get_product(params.product_id)
            if product:
                response_text = f"📋 Product Details:\n{product.get('name', product.get('product_name', 'Unknown'))} - {product.get('category', product.get('product_category', 'N/A'))} - Quantity: {product.get('product_quantity', product.get('price', 0))}"
                action = "get"
            else:
                response_text = f"❌ Product with ID '{params.product_id}' not found."
                action = "get_error"
                
        else:
            response_text = """🤖 I can help you with product operations:

**CREATE**: "Add a new fiber product", "Create mobile service", "Add TV package"
**READ**: "Show all products", "Find fiber products", "Get product 1"
**UPDATE**: "Update product 1 quantity to 500", "Change product 2 quantity to 300" 
**DELETE**: "Delete product 3", "Remove product 5"

Try any of these commands!"""
            action = "help"
        
        # Load updated products after operation
        products = data_manager.get_all_products()
        
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
    print("🚀 Starting SLT Telecom Unified MCP Server")
    print("📋 MCP Tools: process_query (handles all CRUD operations)")
    print("🌐 HTTP Endpoints: /api/v1/Products_DB, /api/v1/chat")
    print("🔗 Frontend: http://localhost:3000")
    print("🔗 Server: http://localhost:8000")
    print("⚡ MCP Protocol: Available via FastMCP")
    
    # Start HTTP server for frontend
    uvicorn.run(
        "unified_mcp_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )