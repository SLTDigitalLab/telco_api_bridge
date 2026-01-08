export interface Product {
  product_id: string;
  product_name: string;
  product_category: string;
  product_quantity: number;
  created_at: string;
  updated_at?: string;
}

export interface ChatMessage {
  id: number;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  products?: Product[];
}

export interface ChatRequest {
  message: string;
  user_id?: string;
}

export interface ChatResponse {
  response: string;
  products?: Product[];
}