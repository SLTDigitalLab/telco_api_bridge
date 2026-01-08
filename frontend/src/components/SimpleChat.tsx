'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Send, User, Bot, MessageSquare } from 'lucide-react';
import { useChatStore } from '@/lib/store';
import { apiClient } from '@/lib/api';
import { ChatMessage } from '@/types/chat';

const TypingIndicator = () => (
  <div className="flex items-center gap-1">
    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
  </div>
);

const MessageBubble = ({ message }: { message: ChatMessage }) => {
  const isUser = message.sender === 'user';

  // Consistent time formatting function that works on both server and client
  const formatTime = (timestamp: Date) => {
    // Use consistent formatting that works in both environments
    const hours = timestamp.getHours().toString().padStart(2, '0');
    const minutes = timestamp.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  };
  
  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <Avatar className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600">
          <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
            <Bot className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      )}
      
      <div className={`max-w-[80%] ${isUser ? 'order-first' : ''}`}>
        <div
          className={`px-4 py-3 rounded-2xl ${
            isUser
              ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white ml-auto'
              : 'bg-white border border-gray-200 text-gray-800'
          } shadow-sm`}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {message.text}
          </p>
        </div>
        
        <p className={`text-xs text-gray-500 mt-1 ${
          isUser ? 'text-right' : 'text-left'
        }`}>
          {formatTime(message.timestamp)}
        </p>

        {/* Show products if available */}
        {message.products && message.products.length > 0 && (
          <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm font-medium text-blue-800 mb-2">
              Found {message.products.length} products:
            </p>
            <div className="space-y-1">
              {message.products.slice(0, 3).map((product) => (
                <div key={product.product_id} className="text-sm text-blue-700">
                  <span className="font-medium">{product.product_name}</span>
                  <span className="text-blue-600 ml-2">({product.product_category})</span>
                </div>
              ))}
              {message.products.length > 3 && (
                <p className="text-sm text-blue-600">...and {message.products.length - 3} more</p>
              )}
            </div>
          </div>
        )}
      </div>
      
      {isUser && (
        <Avatar className="w-8 h-8 bg-gradient-to-r from-gray-500 to-gray-600">
          <AvatarFallback className="bg-gradient-to-r from-gray-500 to-gray-600 text-white">
            <User className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  );
};

const SimpleChat = () => {
  const { messages, isLoading, addMessage, setLoading } = useChatStore();
  const [localInput, setLocalInput] = useState('');

  const handleSendMessage = async () => {
    if (!localInput.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now(),
      text: localInput,
      sender: 'user',
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setLocalInput('');
    setLoading(true);

    try {
      const response = await apiClient.sendMessage({ message: localInput });
      
      const botMessage: ChatMessage = {
        id: Date.now() + 1,
        text: response.response,
        sender: 'bot',
        timestamp: new Date(),
        products: response.products
      };
      
      addMessage(botMessage);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error. Please try again later.',
        sender: 'bot',
        timestamp: new Date(),
      };
      
      addMessage(errorMessage);
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="w-full bg-white/80 backdrop-blur-sm border-0 shadow-xl">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <MessageSquare className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">
            SLT Assistant
          </h2>
          <span className="bg-green-100 text-green-800 text-sm font-medium px-2 py-1 rounded-full">
            Online
          </span>
        </div>

        {/* Chat Messages */}
        <ScrollArea className="h-96 mb-6 pr-4">
          <div className="space-y-6">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            
            {isLoading && (
              <div className="flex gap-3">
                <Avatar className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600">
                  <AvatarFallback className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                    <Bot className="w-4 h-4" />
                  </AvatarFallback>
                </Avatar>
                <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl shadow-sm">
                  <TypingIndicator />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="flex gap-3">
          <Textarea
            value={localInput}
            onChange={(e) => setLocalInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about SLT products, fiber broadband, PeoTV, mobile services..."
            className="flex-1 min-h-[60px] max-h-32 resize-none border-gray-200 focus:border-blue-500 focus:ring-blue-500"
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!localInput.trim() || isLoading}
            className="h-auto px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white border-0"
          >
            <Send className="w-5 h-5" />
          </Button>
        </div>

        <div className="mt-4 text-center">
          <p className="text-xs text-gray-500">
            Try asking: &ldquo;Show me fiber products&rdquo; or &ldquo;What mobile services do you have?&rdquo;
          </p>
        </div>
      </div>
    </Card>
  );
};

export default SimpleChat;