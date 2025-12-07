"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardBody, CardHeader } from "@heroui/card";
import { Input } from "@heroui/input";
import { Button } from "@heroui/button";
import { Bot, Send, Loader2 } from "lucide-react";
import axios from "@/lib/axios";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export default function BotPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Привет! Я AI ассистент системы PromTech. Могу помочь с вопросами о данных, статистике, объектах и обследованиях. Чем могу помочь?",
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await axios.post("/bot/chat", {
        message: input.trim(),
      });

      const assistantMessage: Message = {
        role: "assistant",
        content: response.data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const errorMessage: Message = {
        role: "assistant",
        content: error.response?.data?.detail || "Произошла ошибка при обработке запроса. Попробуйте еще раз.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <main className="p-4 md:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">AI Ассистент</h1>
        <p className="text-primary-foreground">
          Задайте вопросы о данных системы, статистике, объектах и обследованиях
        </p>
      </div>

      <Card className="border border-divider h-[calc(100vh-200px)] flex flex-col">
        <CardHeader className="pb-3 border-b border-divider">
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5" />
            <h2 className="text-lg font-semibold">Чат с AI ассистентом</h2>
          </div>
        </CardHeader>
        <CardBody className="flex-1 flex flex-col p-0 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-default-100 text-default-foreground"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {message.role === "assistant" && (
                      <Bot className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <p className="whitespace-pre-wrap break-words">{message.content}</p>
                      <p className="text-xs opacity-70 mt-1">
                        {message.timestamp.toLocaleTimeString("ru-RU", {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-default-100 rounded-lg p-3">
                  <Loader2 className="h-4 w-4 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-divider p-4">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Введите ваш вопрос..."
                disabled={loading}
                className="flex-1"
                endContent={
                  <Button
                    isIconOnly
                    size="sm"
                    color="primary"
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    isLoading={loading}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                }
              />
            </div>
          </div>
        </CardBody>
      </Card>
    </main>
  );
}

