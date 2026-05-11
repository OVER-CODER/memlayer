'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { workspacesAPI, chatsAPI, memoriesAPI } from '@/lib/api';
import { Workspace, Chat, Message, ChatQueryResponse, RetrievedMemory } from '@/types';
import Link from 'next/link';
import { MemoryVisualizer } from '@/components/MemoryVisualizer';

export default function WorkspacePage() {
  const params = useParams();
  const router = useRouter();
  const workspaceId = params.workspace_id as string;

  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChat, setCurrentChat] = useState<Chat | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState('');
  const [showMemories, setShowMemories] = useState(false);
  const [retrievedMemories, setRetrievedMemories] = useState<RetrievedMemory[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadWorkspace();
    loadChats();
  }, [workspaceId]);

  useEffect(() => {
    if (currentChat) {
      loadMessages();
    }
  }, [currentChat]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadWorkspace = async () => {
    try {
      const response = await workspacesAPI.get(workspaceId);
      setWorkspace(response.data);
    } catch (error) {
      console.error('Failed to load workspace:', error);
    }
  };

  const loadChats = async () => {
    try {
      const response = await workspacesAPI.list(100, 0);
      // For now, create a default chat if none exist
      const allChats = response.data[0]?.chats || [];
      if (allChats.length === 0) {
        const newChat = await chatsAPI.create(workspaceId, 'Main Chat');
        setChats([newChat.data]);
        setCurrentChat(newChat.data);
      } else {
        setChats(allChats);
        setCurrentChat(allChats[0]);
      }
    } catch (error) {
      console.error('Failed to load chats:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async () => {
    if (!currentChat) return;
    try {
      const response = await chatsAPI.getMessages(currentChat.id);
      setMessages(response.data);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const createNewChat = async () => {
    try {
      const response = await chatsAPI.create(workspaceId);
      const newChat = response.data;
      setChats([...chats, newChat]);
      setCurrentChat(newChat);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!input.trim() || !currentChat || sending) return;

    const userMessage = input;
    setInput('');
    setSending(true);

    try {
      // Send query to backend
      const response = await chatsAPI.query(currentChat.id, userMessage, 5);
      const result: ChatQueryResponse = response.data;

      // Add messages to UI
      const newMessages: Message[] = [
        {
          id: `temp-user-${Date.now()}`,
          chat_id: currentChat.id,
          role: 'user',
          content: userMessage,
          created_at: new Date().toISOString(),
        },
        {
          id: result.message_id,
          chat_id: currentChat.id,
          role: 'assistant',
          content: result.response,
          created_at: new Date().toISOString(),
        },
      ];

      setMessages([...messages, ...newMessages]);

      // Show memory preview
      if (result.retrieved_memories.length > 0) {
        setRetrievedMemories(result.retrieved_memories);
        setShowMemories(true);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Add error message
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        chat_id: currentChat.id,
        role: 'assistant',
        content: 'Failed to process your message. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages([...messages, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">Loading...</p>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-600">Workspace not found</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-md flex flex-col">
        <div className="p-6 border-b">
          <Link href="/" className="text-sm text-blue-600 hover:text-blue-700">
            ← Back to Workspaces
          </Link>
          <h2 className="text-lg font-semibold mt-4">{workspace.name}</h2>
          <p className="text-xs text-gray-600 mt-1">{workspace.description}</p>
          
          <Link 
            href={`/workspace/${workspaceId}/memories`}
            className="block mt-4 text-sm text-purple-600 hover:text-purple-700 font-medium"
          >
            📊 Memory Inspector
          </Link>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <button
            onClick={createNewChat}
            className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 mb-4 text-sm"
          >
            + New Chat
          </button>

          <div className="space-y-2">
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => setCurrentChat(chat)}
                className={`w-full text-left px-4 py-2 rounded-lg text-sm transition ${
                  currentChat?.id === chat.id
                    ? 'bg-blue-100 text-blue-900'
                    : 'hover:bg-gray-100'
                }`}
              >
                {chat.title}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500">Start a conversation...</p>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-md px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-200 text-gray-900'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-gray-200 text-gray-900 px-4 py-2 rounded-lg">
                    <p>Thinking...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Memory Inspector Toggle */}
        {showMemories && (
          <div className="border-t border-gray-300 bg-gray-50">
            <MemoryVisualizer 
              memories={retrievedMemories}
              isOpen={showMemories}
              onClose={() => setShowMemories(false)}
            />
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-gray-300 p-4 bg-white">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Type your message..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={sending}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSendMessage}
              disabled={sending || !input.trim()}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
