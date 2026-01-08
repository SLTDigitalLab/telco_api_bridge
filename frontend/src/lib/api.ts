export interface Product {
  product_id: string;
  product_name: string;
  product_category: string;
  product_quantity: number;
  created_at: string;
  updated_at?: string;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  page: number;
  per_page: number;
}

export interface ChatRequest {
  message: string;
  user_id?: string;
}

export interface ChatResponse {
  response: string;
  products?: Product[];
  action_performed?: string;
  success?: boolean;
}

export interface ProductCreate {
  product_id: string;
  product_name: string;
  product_category: string;
  product_quantity: number;
}

export interface ProductUpdate {
  product_name?: string;
  product_category?: string;
  product_quantity?: number;
}

class ApiClient {
  private getBackendUrl(): string {
    // Connect to your SLT backend
    return process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';
  }

  async getProducts(search?: string, category?: string): Promise<Product[]> {
    const baseUrl = `${this.getBackendUrl()}/api/v1/Products_DB`;
    const params = new URLSearchParams();
    
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    
    const url = params.toString() ? `${baseUrl}?${params}` : baseUrl;
    
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.products || data; // Handle different response formats
  }

  async getProduct(productId: string): Promise<Product> {
    const response = await fetch(`${this.getBackendUrl()}/api/v1/Products_DB/${productId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async createProduct(product: ProductCreate): Promise<Product> {
    const response = await fetch(`${this.getBackendUrl()}/api/v1/Add-Product`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(product),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async updateProduct(productId: string, updates: ProductUpdate): Promise<Product> {
    const response = await fetch(`${this.getBackendUrl()}/api/v1/Update-Product/${productId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async deleteProduct(productId: string): Promise<boolean> {
    const response = await fetch(`${this.getBackendUrl()}/api/v1/Delete-Product/${productId}`, {
      method: 'DELETE',
    });
    
    return response.ok;
  }

  async searchProductsByCategory(category: string): Promise<Product[]> {
    const response = await fetch(`${this.getBackendUrl()}/api/v1/Products_DB/search/category/${category}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async searchProductsByName(name: string): Promise<Product[]> {
    const response = await fetch(`${this.getBackendUrl()}/api/v1/Products_DB/search/name/${name}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  async searchProducts(query: string): Promise<ChatResponse> {
    // This could be extended to use AI/NLP for product queries
    // For now, we'll do simple search
    try {
      const products = await this.getProducts(query);
      return {
        response: products.length > 0 
          ? `Found ${products.length} products matching "${query}"` 
          : `No products found matching "${query}"`,
        products
      };
    } catch (error) {
      return {
        response: `Sorry, I couldn't search for products at the moment. Please try again.`,
        products: []
      };
    }
  }

  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.getBackendUrl()}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: request.message,
          user_id: request.user_id || 'anonymous'
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        response: data.response,
        products: data.products || [],
        action_performed: data.action_performed,
        success: data.success
      };
    } catch (error) {
      console.error('Chat API error:', error);
      return {
        response: "I'm sorry, I couldn't process your request right now. Please check that the backend is running and try again.",
        products: [],
        action_performed: 'error',
        success: false
      };
    }
  }
}

export const apiClient = new ApiClient();