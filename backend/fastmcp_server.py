#!/usr/bin/env python3
"""
SLT Telecom API Bridge - FastMCP Server
Standalone MCP server using FastMCP for product database operations
"""

from fastmcp import FastMCP
from typing import Dict, List, Any, Optional
import json
import os
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


class JSONDataManager:
    def __init__(self, data_file: str):
        self.data_file = data_file
        self.ensure_data_file()
    
    def ensure_data_file(self):
        """Ensure the data file exists with initial data"""
        if not os.path.exists(self.data_file):
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            initial_data = {
                "products": [
                    {
                        "id": "1",
                        "name": "SLT Fiber 100Mbps",
                        "category": "Internet",
                        "price": 5990.0,
                        "description": "High-speed fiber internet connection with 100Mbps download speed",
                        "features": ["100Mbps Download", "20Mbps Upload", "Unlimited Data", "WiFi Router Included"]
                    },
                    {
                        "id": "2", 
                        "name": "SLT PEO TV Premium",
                        "category": "Television",
                        "price": 1500.0,
                        "description": "Premium IPTV service with local and international channels",
                        "features": ["150+ Channels", "HD Quality", "Catch-up TV", "Mobile App Access"]
                    }
                ]
            }
            with open(self.data_file, 'w') as f:
                json.dump(initial_data, f, indent=2)
    
    def load_data(self) -> Dict:
        """Load data from JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"products": []}
    
    def save_data(self, data: Dict):
        """Save data to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def search_products(self, search_term: str) -> List[Dict]:
        """Search for products by name or category"""
        data = self.load_data()
        products = data.get("products", [])
        
        if not search_term:
            return products
        
        search_term = search_term.lower()
        results = []
        for product in products:
            if (search_term in product.get("name", "").lower() or 
                search_term in product.get("category", "").lower() or
                search_term in product.get("description", "").lower()):
                results.append(product)
        
        return results
    
    def get_product(self, product_id: str) -> Optional[Dict]:
        """Get a specific product by ID"""
        data = self.load_data()
        products = data.get("products", [])
        
        for product in products:
            if product.get("id") == product_id:
                return product
        
        return None
    
    def create_product(self, product_data: Dict) -> Dict:
        """Create a new product"""
        data = self.load_data()
        products = data.get("products", [])
        
        # Generate new ID
        max_id = max([int(p.get("id", "0")) for p in products] + [0])
        product_data["id"] = str(max_id + 1)
        
        products.append(product_data)
        data["products"] = products
        self.save_data(data)
        
        return product_data
    
    def update_product(self, product_id: str, product_data: Dict) -> Optional[Dict]:
        """Update an existing product"""
        data = self.load_data()
        products = data.get("products", [])
        
        for i, product in enumerate(products):
            if product.get("id") == product_id:
                product_data["id"] = product_id  # Ensure ID is preserved
                products[i] = product_data
                data["products"] = products
                self.save_data(data)
                return product_data
        
        return None
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product by ID"""
        data = self.load_data()
        products = data.get("products", [])
        
        for i, product in enumerate(products):
            if product.get("id") == product_id:
                products.pop(i)
                data["products"] = products
                self.save_data(data)
                return True
        
        return False


class NaturalLanguageProcessor:
    def __init__(self):
        self.patterns = {
            QueryType.SEARCH: [
                r"find|search|look for|show me|list",
                r"products|items|services"
            ],
            QueryType.GET: [
                r"get|show|display|details of",
                r"product|item|service",
                r"id|with id"
            ],
            QueryType.CREATE: [
                r"create|add|new|insert",
                r"product|item|service"
            ],
            QueryType.UPDATE: [
                r"update|modify|edit|change",
                r"product|item|service"
            ],
            QueryType.DELETE: [
                r"delete|remove|drop",
                r"product|item|service"
            ]
        }
    
    def extract_query_params(self, query: str) -> QueryParams:
        """Extract query parameters from natural language"""
        query_lower = query.lower()
        query_type = QueryType.UNKNOWN
        
        # Determine query type
        for qtype, patterns in self.patterns.items():
            if any(pattern in query_lower for pattern_list in patterns for pattern in pattern_list.split("|")):
                query_type = qtype
                break
        
        # Extract parameters
        product_id = None
        search_term = None
        product_data = None
        
        # Extract product ID if present
        import re
        id_match = re.search(r'\bid[:\s]*(["\']?)(\w+)\1', query_lower)
        if id_match:
            product_id = id_match.group(2)
        
        # Extract search terms
        if query_type == QueryType.SEARCH:
            # Remove common words and extract meaningful terms
            stop_words = {"find", "search", "look", "for", "show", "me", "list", "products", "items", "services"}
            words = query_lower.split()
            search_words = [w for w in words if w not in stop_words and len(w) > 2]
            if search_words:
                search_term = " ".join(search_words)
        
        return QueryParams(
            query_type=query_type,
            product_id=product_id,
            search_term=search_term,
            product_data=product_data
        )


# Initialize FastMCP
mcp = FastMCP("SLT Telecom MCP Server")

# Initialize data manager and NL processor
data_manager = JSONDataManager("data/products.json")
nl_processor = NaturalLanguageProcessor()


@mcp.tool()
def process_query(query: str) -> str:
    """Process natural language queries for product database operations"""
    params = nl_processor.extract_query_params(query)
    
    try:
        if params.query_type == QueryType.SEARCH:
            results = data_manager.search_products(params.search_term or "")
            if results:
                return f"Found {len(results)} products:\n" + "\n".join([
                    f"- {p['name']} (ID: {p['id']}) - {p.get('category', 'N/A')} - LKR {p.get('price', 0)}"
                    for p in results
                ])
            else:
                return "No products found matching your search criteria."
                
        elif params.query_type == QueryType.GET:
            if not params.product_id:
                return "Please specify a product ID to retrieve details."
            
            product = data_manager.get_product(params.product_id)
            if product:
                return f"Product Details:\n" + json.dumps(product, indent=2)
            else:
                return f"Product with ID '{params.product_id}' not found."
                
        else:
            return f"Query type '{params.query_type.value}' identified. For create/update/delete operations, please use the specific tools."
            
    except Exception as e:
        return f"Error processing query: {str(e)}"


@mcp.tool()
def search_products(search_term: str = "") -> str:
    """Search for products by name, category, or description"""
    try:
        results = data_manager.search_products(search_term)
        if results:
            return json.dumps(results, indent=2)
        else:
            return "No products found matching your search criteria."
    except Exception as e:
        return f"Error searching products: {str(e)}"


@mcp.tool()
def get_product(product_id: str) -> str:
    """Get details of a specific product by ID"""
    try:
        product = data_manager.get_product(product_id)
        if product:
            return json.dumps(product, indent=2)
        else:
            return f"Product with ID '{product_id}' not found."
    except Exception as e:
        return f"Error retrieving product: {str(e)}"


@mcp.tool()
def create_product(name: str, category: str, price: float, description: str, features: List[str]) -> str:
    """Create a new product"""
    try:
        product_data = {
            "name": name,
            "category": category,
            "price": price,
            "description": description,
            "features": features
        }
        result = data_manager.create_product(product_data)
        return f"Product created successfully with ID: {result['id']}\n" + json.dumps(result, indent=2)
    except Exception as e:
        return f"Error creating product: {str(e)}"


@mcp.tool()
def update_product(product_id: str, name: str, category: str, price: float, description: str, features: List[str]) -> str:
    """Update an existing product"""
    try:
        product_data = {
            "name": name,
            "category": category,
            "price": price,
            "description": description,
            "features": features
        }
        result = data_manager.update_product(product_id, product_data)
        if result:
            return f"Product updated successfully:\n" + json.dumps(result, indent=2)
        else:
            return f"Product with ID '{product_id}' not found."
    except Exception as e:
        return f"Error updating product: {str(e)}"


@mcp.tool()
def delete_product(product_id: str) -> str:
    """Delete a product by ID"""
    try:
        success = data_manager.delete_product(product_id)
        if success:
            return f"Product with ID '{product_id}' deleted successfully."
        else:
            return f"Product with ID '{product_id}' not found."
    except Exception as e:
        return f"Error deleting product: {str(e)}"


if __name__ == "__main__":
    mcp.run()