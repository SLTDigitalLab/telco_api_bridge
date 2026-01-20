import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Bot, User, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import clsx from "clsx";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';


interface Message {
    role: "user" | "assistant" | "tool";
    content: string;
}

function App() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isLoading]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMessage: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMessage]);
        setInput("");
        setIsLoading(true);

        const history = [...messages, userMessage].filter(m => m.role !== 'tool');

        try {
            // Create a placeholder for the bot message
            const botMessage: Message = { role: "assistant", content: "" };
            setMessages((prev) => [...prev, botMessage]);

            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ messages: history })
            });

            if (!response.body) throw new Error("No response body");

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let accumulatedContent = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value, { stream: true });
                accumulatedContent += text;

                // Update the last message (bot message) with new content
                setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMsg = newMessages[newMessages.length - 1];
                    if (lastMsg.role === "assistant") {
                        lastMsg.content = accumulatedContent;
                    }
                    return newMessages;
                });
            }

        } catch (error) {
            console.error("Error sending message:", error);
            setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "⚠️ Error: Connection interrupted." }
            ]);
        } finally {
            setIsLoading(false);
        }
    };


    const handleClear = () => {
        setMessages([]);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="flex flex-col h-screen bg-[#0f1014] text-gray-100 font-sans selection:bg-indigo-500/30">
            {/* Header */}
            <header className="flex items-center justify-between px-8 py-5 border-b border-white/5 bg-white/[0.02] backdrop-blur-xl sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/20">
                        <Bot className="w-6 h-6 text-white" />
                    </div>
                    <div>
                        <h1 className="text-xl font-semibold bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                            HR Agent
                        </h1>
                        <p className="text-xs text-gray-500 font-medium tracking-wide">ENTERPRISE ASSISTANT</p>
                    </div>
                </div>
                <button
                    onClick={handleClear}
                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors rounded-lg hover:bg-white/5"
                >
                    <Trash2 className="w-4 h-4" />
                    Clear Chat
                </button>
            </header>

            {/* Chat Area */}
            <main className="flex-1 overflow-y-auto px-4 py-8 custom-scrollbar">
                <div className="max-w-3xl mx-auto space-y-6">
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-4 opacity-50">
                            <div className="p-4 rounded-full bg-white/5">
                                <Sparkles className="w-8 h-8 text-indigo-400" />
                            </div>
                            <p className="text-lg font-medium">How can I assist you today?</p>
                        </div>
                    )}

                    <AnimatePresence initial={false}>
                        {messages.map((msg, index) => {
                            // --- FIX START ---
                            // If this is an assistant message and it is empty, DO NOT render it yet.
                            // This prevents the empty gray box. The "Thinking..." dots will show instead.
                            if (msg.role === "assistant" && !msg.content) {
                                return null;
                            }
                            // --- FIX END ---

                            return (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className={clsx(
                                        "flex gap-4",
                                        msg.role === "user" ? "justify-end" : "justify-start"
                                    )}
                                >
                                    {msg.role !== "user" && (
                                        <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-1">
                                            <Bot className="w-5 h-5 text-indigo-400" />
                                        </div>
                                    )}

                                    <div
                                        className={clsx(
                                            "max-w-[80%] rounded-2xl px-6 py-4 text-sm leading-relaxed shadow-sm",
                                            msg.role === "user"
                                                ? "bg-indigo-600 text-white rounded-br-none"
                                                : "bg-white/5 border border-white/10 text-gray-200 rounded-bl-none backdrop-blur-sm"
                                        )}
                                    >
                                        {/* 1. WRAPPER DIV: Put the 'prose' classes here */}
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown
                                                remarkPlugins={[remarkGfm]}
                                                // 2. Remove className from here
                                                components={{
                                                    p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                                                    strong: ({ node, ...props }) => <span className="font-bold text-white" {...props} />,
                                                    ul: ({ node, ...props }) => <ul className="list-disc pl-4 mb-2 space-y-1" {...props} />,
                                                    ol: ({ node, ...props }) => <ol className="list-decimal pl-4 mb-2 space-y-1" {...props} />,
                                                    li: ({ node, ...props }) => <li className="marker:text-gray-400" {...props} />,
                                                    a: ({ node, ...props }) => <a className="text-indigo-400 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
                                                }}
                                            >
                                                {msg.content}
                                            </ReactMarkdown>
                                        </div>
                                    </div>

                                    {msg.role === "user" && (
                                        <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0 mt-1">
                                            <User className="w-5 h-5 text-gray-300" />
                                        </div>
                                    )}
                                </motion.div>
                            );
                        })}
                    </AnimatePresence>

                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex gap-4 justify-start"
                        >
                            <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                                <Bot className="w-5 h-5 text-indigo-400" />
                            </div>
                            <div className="flex items-center gap-1.5 px-6 py-4 bg-white/5 border border-white/10 rounded-2xl rounded-bl-none">
                                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                            </div>
                        </motion.div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </main>

            {/* Input Area */}
            <footer className="p-6 border-t border-white/5 bg-[#0f1014]">
                <div className="max-w-3xl mx-auto relative">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your request here..."
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-6 py-4 pr-16 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent transition-all shadow-lg"
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isLoading}
                        className="absolute right-2 top-2 p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
                <p className="text-center text-xs text-gray-600 mt-4">
                    AI can make mistakes. Please verify important information.
                </p>
            </footer>
        </div>
    );
}

export default App;
