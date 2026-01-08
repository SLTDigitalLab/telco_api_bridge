import { create } from 'zustand';
import { ChatMessage, Product } from '@/types/chat';

interface ChatStore {
  messages: ChatMessage[];
  products: Product[];
  isLoading: boolean;
  inputText: string;
  addMessage: (message: ChatMessage) => void;
  setLoading: (loading: boolean) => void;
  setInputText: (text: string) => void;
  setProducts: (products: Product[]) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [
    {
      id: 1,
      text: "Hello! I'm your SLT DBMS Assistant. I can help you perform full CRUD operations on our company database. Try asking me to:\n\n• 'show all products' - View all products\n• 'add product PROD999 named Ultra Fiber in Internet Services with quantity 50' - Create new products\n• 'update product PROD001 quantity to 100' - Modify existing products\n• 'delete product PROD002' - Remove products\n• 'search for fiber products' - Find specific items\n\nWhat would you like to do?",
      sender: 'bot',
      timestamp: new Date('2024-01-01T12:00:00.000Z')
    }
  ],
  products: [],
  isLoading: false,
  inputText: '',
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setLoading: (loading) => set({ isLoading: loading }),
  setInputText: (text) => set({ inputText: text }),
  setProducts: (products) => set({ products }),
  clearMessages: () =>
    set({
      messages: [
        {
          id: 1,
          text: "Hello! I'm your SLT Telecom Assistant. I can help you find information about our products like Fiber Broadband, PeoTV, Mobile services, and more. What would you like to know?",
          sender: 'bot',
          timestamp: new Date('2024-01-01T12:00:00.000Z')
        }
      ]
    }),
}));