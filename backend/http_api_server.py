#!/usr/bin/env python3
"""
SLT Telecom API Bridge - HTTP API Server
HTTP REST API wrapper for the FastMCP server to enable frontend communication
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import uvicorn
from datetime import datetime


class Product(BaseModel):
    product_id: str
    product_name: str
    product_category: str
    product_quantity: int
    created_at: str = ""
    updated_at: Optional[str] = None


class ProductCreate(BaseModel):
    product_name: str
    product_category: str
    product_quantity: int


class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    product_quantity: Optional[int] = None


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
                        "product_id": "SLT001",
                        "product_name": "Fiber Broadband 100Mbps",
                        "product_category": "Internet Services",
                        "product_quantity": 500,
                        "created_at": "2024-01-15T10:00:00Z"
                    },
                    {
                        "product_id": "SLT002",
                        "product_name": "PeoTV Entertainment Package",
                        "product_category": "Digital TV",
                        "product_quantity": 300,
                        "created_at": "2024-01-15T10:00:00Z"
                    },
                    {
                        "product_id": "SLT003",
                        "product_name": "SLT Mobitel 4G SIM Card",
                        "product_category": "Mobile Services",
                        "product_quantity": 1000,
                        "created_at": "2024-01-15T10:00:00Z"
                    },
                    {
                        "product_id": "SLT004",
                        "product_name": "Fiber Broadband 200Mbps",
                        "product_category": "Internet Services",
                        "product_quantity": 250,
                        "created_at": "2024-01-16T09:00:00Z"
                    },
                    {
                        "product_id": "SLT005",
                        "product_name": "Business Internet Package",
                        "product_category": "Internet Services",
                        "product_quantity": 150,
                        "created_at": "2024-01-16T09:00:00Z"
                    },
                    {
                        "product_id": "SLT006",
                        "product_name": "International Roaming Plan",
                        "product_category": "Mobile Services",
                        "product_quantity": 800,
                        "created_at": "2024-01-17T11:00:00Z"
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
    
    def search_products(self, search_term: str = "", category: str = "") -> List[Dict]:
        products = self.get_all_products()
        
        if search_term:
            search_term = search_term.lower()
            products = [p for p in products if (
                search_term in p.get("product_name", "").lower() or 
                search_term in p.get("product_category", "").lower() or
                search_term in p.get("product_id", "").lower()
            )]
        
        if category:
            category = category.lower()
            products = [p for p in products if category in p.get("product_category", "").lower()]
        
        return products
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        products = self.get_all_products()
        for product in products:
            if product.get("product_id") == product_id:
                return product
        return None
    
    def create_product(self, product_data: Dict) -> Dict:
        data = self.load_data()
        products = data.get("products", [])
        
        # Generate new ID
        existing_ids = [p.get("product_id", "") for p in products]
        counter = 1
        while f"SLT{counter:03d}" in existing_ids:
            counter += 1
        
        product_data["product_id"] = f"SLT{counter:03d}"
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


# Initialize FastAPI app
app = FastAPI(
    title="SLT Telecom API Bridge",
    description="HTTP REST API for SLT Telecom product database operations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data manager
data_manager = JSONDataManager("data/products.json")


@app.get("/")
async def root():
    return {
        "message": "SLT Telecom API Bridge",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "products": "/api/v1/Products_DB",
            "chat": "/api/v1/chat",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/Products_DB", response_model=List[Product])
async def get_products(search: str = "", category: str = ""):
    """Get all products or search products"""
    try:
        products = data_manager.search_products(search, category)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/Products_DB/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    try:
        product = data_manager.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/Products_DB", response_model=Product)
async def create_product(product: ProductCreate):
    """Create a new product"""
    try:
        product_data = product.dict()
        new_product = data_manager.create_product(product_data)
        return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/Products_DB/{product_id}", response_model=Product)
async def update_product(product_id: str, product: ProductUpdate):
    """Update an existing product"""
    try:
        product_data = {k: v for k, v in product.dict().items() if v is not None}
        updated_product = data_manager.update_product(product_id, product_data)
        if not updated_product:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/Products_DB/{product_id}")
async def delete_product(product_id: str):
    """Delete a product"""
    try:
        success = data_manager.delete_product(product_id)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        return {"message": "Product deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Handle chat messages and natural language queries"""
    try:
        message = request.message.lower()
        response_text = ""
        products = None
        action = None
        
        # CREATE operations
        if any(word in message for word in ["add", "create", "new", "insert"]):
            if "fiber" in message or "internet" in message or "broadband" in message:
                # Extract details from message
                if any(speed in message for speed in ["500", "1gb", "gigabit", "1000"]):
                    product_data = {
                        "product_name": "Fiber Broadband 1Gbps",
                        "product_category": "Internet Services", 
                        "product_quantity": 100
                    }
                elif "200" in message:
                    product_data = {
                        "product_name": "Fiber Broadband 200Mbps",
                        "product_category": "Internet Services",
                        "product_quantity": 200
                    }
                else:
                    product_data = {
                        "product_name": "Fiber Broadband 300Mbps",
                        "product_category": "Internet Services",
                        "product_quantity": 150
                    }
                
                new_product = data_manager.create_product(product_data)
                response_text = f"✅ Successfully created new product: {new_product['product_name']} (ID: {new_product['product_id']})"
                products = [new_product]
                action = "create"
            
            elif "tv" in message or "peotv" in message:
                product_data = {
                    "product_name": "PeoTV Sports Premium",
                    "product_category": "Digital TV",
                    "product_quantity": 300
                }
                new_product = data_manager.create_product(product_data)
                response_text = f"✅ Successfully created new TV product: {new_product['product_name']} (ID: {new_product['product_id']})"
                products = [new_product]
                action = "create"
            
            elif "mobile" in message or "sim" in message or "mobitel" in message:
                product_data = {
                    "product_name": "SLT Mobitel 5G Premium",
                    "product_category": "Mobile Services",
                    "product_quantity": 500
                }
                new_product = data_manager.create_product(product_data)
                response_text = f"✅ Successfully created new mobile product: {new_product['product_name']} (ID: {new_product['product_id']})"
                products = [new_product]
                action = "create"
            else:
                response_text = "To create a product, please specify the type (fiber/internet, tv, or mobile). Example: 'Add a new fiber product'"
                action = "create_help"
        
        # UPDATE operations
        elif any(word in message for word in ["update", "modify", "change", "edit", "increase", "decrease"]):
            # Extract product ID if mentioned
            import re
            id_match = re.search(r'slt\d+', message)
            if id_match:
                product_id = id_match.group().upper()
                existing_product = data_manager.get_product_by_id(product_id)
                if existing_product:
                    update_data = {}
                    
                    # Quantity updates
                    quantity_match = re.search(r'(\d+)', message)
                    if quantity_match and any(word in message for word in ["quantity", "stock", "amount", "increase", "decrease"]):
                        new_quantity = int(quantity_match.group())
                        if "increase" in message:
                            new_quantity = existing_product.get("product_quantity", 0) + new_quantity
                        update_data["product_quantity"] = new_quantity
                    
                    # Name updates
                    if "name" in message and "to" in message:
                        name_part = message.split("to")[-1].strip()
                        if name_part:
                            update_data["product_name"] = name_part.title()
                    
                    if update_data:
                        updated_product = data_manager.update_product(product_id, update_data)
                        response_text = f"✅ Successfully updated product {product_id}: {updated_product['product_name']}"
                        products = [updated_product]
                        action = "update"
                    else:
                        response_text = f"Please specify what to update for {product_id}. Example: 'Update SLT001 quantity to 500'"
                        action = "update_help"
                else:
                    response_text = f"❌ Product {product_id} not found"
                    action = "update_error"
            else:
                response_text = "To update a product, please specify the product ID. Example: 'Update SLT001 quantity to 500'"
                action = "update_help"
        
        # DELETE operations  
        elif any(word in message for word in ["delete", "remove", "drop"]):
            import re
            id_match = re.search(r'slt\d+', message)
            if id_match:
                product_id = id_match.group().upper()
                existing_product = data_manager.get_product_by_id(product_id)
                if existing_product:
                    success = data_manager.delete_product(product_id)
                    if success:
                        response_text = f"✅ Successfully deleted product {product_id}: {existing_product['product_name']}"
                        products = data_manager.get_all_products()  # Return updated list
                        action = "delete"
                    else:
                        response_text = f"❌ Failed to delete product {product_id}"
                        action = "delete_error"
                else:
                    response_text = f"❌ Product {product_id} not found"
                    action = "delete_error"
            else:
                response_text = "To delete a product, please specify the product ID. Example: 'Delete SLT003'"
                action = "delete_help"
        
        # READ/SEARCH operations
        elif any(word in message for word in ["search", "find", "show", "list", "get"]):
            if "all" in message or "products" in message:
                products = data_manager.get_all_products()
                response_text = f"📋 Found {len(products)} products in the database."
                action = "search"
            elif any(word in message for word in ["fiber", "internet", "broadband"]):
                products = data_manager.search_products("fiber")
                if not products:
                    products = data_manager.search_products("internet")
                response_text = f"🌐 Found {len(products)} fiber/internet products."
                action = "search"
            elif any(word in message for word in ["tv", "television", "peotv"]):
                products = data_manager.search_products("tv")
                response_text = f"📺 Found {len(products)} TV products."
                action = "search"
            elif any(word in message for word in ["mobile", "sim", "mobitel"]):
                products = data_manager.search_products("mobile")
                response_text = f"📱 Found {len(products)} mobile products."
                action = "search"
            else:
                products = data_manager.get_all_products()
                response_text = f"📋 Here are all {len(products)} products in our database."
                action = "search"
        else:
            response_text = """
🤖 I can help you with product operations:

**CREATE**: "Add a new fiber product", "Create a mobile service", "Add TV package"
**READ**: "Show all products", "Find fiber products", "List mobile services"  
**UPDATE**: "Update SLT001 quantity to 500", "Change SLT002 name to New Name"
**DELETE**: "Delete SLT003", "Remove product SLT005"

Try any of these commands!
            """.strip()
            action = "help"
        
        return ChatResponse(
            response=response_text,
            products=products,
            action_performed=action,
            success=True
        )
    except Exception as e:
        return ChatResponse(
            response=f"❌ Error processing request: {str(e)}",
            products=None,
            action_performed="error",
            success=False
        )


if __name__ == "__main__":
    print("🚀 Starting SLT Telecom API Bridge HTTP Server")
    print("📋 Available endpoints:")
    print("   • GET /api/v1/Products_DB - List all products")
    print("   • POST /api/v1/Products_DB - Create product")
    print("   • PUT /api/v1/Products_DB/{id} - Update product")
    print("   • DELETE /api/v1/Products_DB/{id} - Delete product")
    print("   • POST /api/v1/chat - Chat interface")
    print("   • GET /health - Health check")
    print("🌐 Frontend URL: http://localhost:3000")
    print("🔗 API URL: http://localhost:8000")
    
    uvicorn.run(
        "http_api_server:app", 
        host="0.0.0.0", 
        port=8000,
        reload=True
    )