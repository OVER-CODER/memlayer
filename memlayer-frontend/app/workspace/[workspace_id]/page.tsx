'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { workspacesAPI, chatsAPI, api } from '@/lib/api';
import { Workspace, Chat, Message, ChatQueryResponse, RetrievedMemory } from '@/types';
import Link from 'next/link';
import { MemoryVisualizer } from '@/components/MemoryVisualizer';
import { Send, Zap, ChevronLeft, BarChart2, Plus, MessageSquare } from 'lucide-react';

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
  const [coordinating, setCoordinating] = useState(false);
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
    } else {
      setMessages([]);
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
      // Try console API as fallback
      try {
        const diag = await api.console.getWorkspaceDiagnostics(workspaceId);
        if (diag) {
          setWorkspace({
            id: diag.workspace_id,
            workspace_id: diag.workspace_id,
            name: diag.workspace_id,
            provider: diag.provider,
            token_budget: diag.token_budget,
            memory_count: diag.memory_count,
            created_at: diag.created_at,
            updated_at: diag.updated_at
          });
        }
      } catch (err) {
        console.error('Failed to load workspace from console:', err);
      }
    }
  };

  const loadChats = async () => {
    try {
      const response = await chatsAPI.list(workspaceId, 50, 0);
      const allChats = response.data || [];
      setChats(allChats);
      if (allChats.length > 0 && !currentChat) {
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
      const response = await chatsAPI.create(workspaceId, `New Chat ${chats.length + 1}`);
      const newChat = response.data;
      setChats([newChat, ...chats]);
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
      // Add user message optimistically
      const tempUserMsg: Message = {
        id: `temp-user-${Date.now()}`,
        chat_id: currentChat.id,
        role: 'user',
        content: userMessage,
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, tempUserMsg]);

      // Send query to backend
      const response = await chatsAPI.query(currentChat.id, userMessage, 5);
      const result: ChatQueryResponse = response.data;

      // Add assistant message
      const assistantMsg: Message = {
        id: result.message_id,
        chat_id: currentChat.id,
        role: 'assistant',
        content: result.response,
        created_at: new Date().toISOString(),
      };

      setMessages(prev => [...prev, assistantMsg]);

      // Show memory preview if any
      if (result.retrieved_memories && result.retrieved_memories.length > 0) {
        setRetrievedMemories(result.retrieved_memories);
        setShowMemories(true);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        chat_id: currentChat.id,
        role: 'assistant',
        content: 'Failed to process your message. Please verify backend connectivity.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const runCoordination = async () => {
    if (coordinating || !workspace) return;
    setCoordinating(true);
    try {
      const res = await api.console.coordinate(workspaceId, "Perform semantic reconciliation and generate views.");
      // We don't necessarily show the result in chat, but it triggers the backend systems
      // which will then show up in Telemetry, Coordination Graph, etc.
      alert(`Coordination successful: ${res.report_id}`);
    } catch (error) {
      console.error('Coordination failed:', error);
      alert('Coordination failed. Check console.');
    } finally {
      setCoordinating(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-900">
        <div className="text-slate-400 animate-pulse">Synchronizing Cognition...</div>
      </div>
    );
  }

  if (!workspace) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 p-4">
        <div className="text-white text-xl mb-4">Workspace not found</div>
        <Link href="/workspaces" className="text-indigo-400 hover:underline flex items-center">
          <ChevronLeft className="w-4 h-4 mr-1" /> Return to Workspaces
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-slate-900 overflow-hidden">
      {/* Sidebar */}
      <div className="w-72 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-800">
          <Link href="/workspaces" className="text-xs text-slate-500 hover:text-slate-300 flex items-center mb-4 transition-colors">
            <ChevronLeft className="w-3 h-3 mr-1" /> ALL WORKSPACES
          </Link>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white truncate mr-2" title={workspace.name}>{workspace.name}</h2>
            <div className="bg-indigo-500/10 text-indigo-400 text-[10px] px-1.5 py-0.5 rounded border border-indigo-500/20 font-mono">
              {workspace.provider}
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-1 truncate">{workspace.description || 'Cognitive memory bound'}</p>
          
          <div className="grid grid-cols-2 gap-2 mt-4">
            <Link 
              href={`/workspace/${workspaceId}/memories`}
              className="flex items-center justify-center py-2 px-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded text-[10px] text-slate-300 transition-colors"
            >
              <BarChart2 className="w-3 h-3 mr-1.5 text-blue-400" /> MEMORIES
            </Link>
            <button 
              onClick={runCoordination}
              disabled={coordinating}
              className="flex items-center justify-center py-2 px-1 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded text-[10px] text-slate-300 transition-colors disabled:opacity-50"
            >
              <Zap className={`w-3 h-3 mr-1.5 ${coordinating ? 'animate-pulse text-amber-400' : 'text-amber-500'}`} /> 
              {coordinating ? 'SYNCING...' : 'COORDINATE'}
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2 px-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Conversations</span>
              <button onClick={createNewChat} className="text-slate-500 hover:text-white transition-colors">
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-1">
              {chats.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => setCurrentChat(chat)}
                  className={`w-full text-left px-3 py-2 rounded-md text-sm transition-all group flex items-center ${
                    currentChat?.id === chat.id
                      ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent'
                  }`}
                >
                  <MessageSquare className={`w-3.5 h-3.5 mr-2 ${currentChat?.id === chat.id ? 'text-indigo-400' : 'text-slate-600'}`} />
                  <span className="truncate">{chat.title}</span>
                </button>
              ))}
              {chats.length === 0 && (
                <div className="px-3 py-4 text-center border border-dashed border-slate-800 rounded-lg">
                  <p className="text-[10px] text-slate-600">No active chats</p>
                  <button onClick={createNewChat} className="text-[10px] text-indigo-400 hover:underline mt-1">Start New Session</button>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-slate-800">
           <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono">
              <span>MEMORIES</span>
              <span className="text-slate-300">{workspace.memory_count || 0}</span>
           </div>
           <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono mt-1">
              <span>BUDGET</span>
              <span className="text-slate-300">{workspace.token_budget || 4000}</span>
           </div>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative bg-slate-900 shadow-2xl">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!currentChat ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
              <div className="w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center">
                <MessageSquare className="w-8 h-8 text-slate-600" />
              </div>
              <div>
                <h3 className="text-white font-medium">Select a conversation</h3>
                <p className="text-slate-500 text-sm">Or start a new cognitive session to begin.</p>
              </div>
              <button 
                onClick={createNewChat}
                className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Create New Chat
              </button>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-2 opacity-50">
              <Zap className="w-8 h-8 text-indigo-500 mb-2" />
              <p className="text-slate-400 text-sm">The semantic runtime is ready.</p>
              <p className="text-slate-600 text-xs">Send a message to initialize memory retrieval.</p>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto w-full space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] px-4 py-3 rounded-2xl shadow-sm ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-tr-none'
                        : 'bg-slate-800 text-slate-200 rounded-tl-none border border-slate-700'
                    }`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    <div className={`text-[10px] mt-2 opacity-40 font-mono ${msg.role === 'user' ? 'text-right' : 'text-left'}`}>
                      {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                </div>
              ))}
              {sending && (
                <div className="flex justify-start">
                  <div className="bg-slate-800 text-slate-400 px-4 py-3 rounded-2xl rounded-tl-none border border-slate-700 flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-1.5 h-1.5 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-xs font-medium ml-2">Kernel Processing...</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Memory Visualizer Overlay */}
        {showMemories && retrievedMemories.length > 0 && (
          <div className="absolute inset-x-0 bottom-24 z-20 px-6 pointer-events-none">
            <div className="max-w-4xl mx-auto pointer-events-auto">
               <MemoryVisualizer 
                memories={retrievedMemories}
                isOpen={showMemories}
                onClose={() => setShowMemories(false)}
              />
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="p-6 bg-slate-900/80 backdrop-blur-md border-t border-slate-800 sticky bottom-0">
          <div className="max-w-4xl mx-auto flex gap-3 relative">
            <div className="flex-1 relative group">
              <input
                type="text"
                placeholder={currentChat ? "Send a message to the cognition substrate..." : "Select a chat first..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                disabled={sending || !currentChat}
                className="w-full bg-slate-950 text-slate-200 pl-4 pr-12 py-3.5 border border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all text-sm group-hover:border-slate-700 disabled:opacity-50"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center space-x-1">
                 <button
                  onClick={handleSendMessage}
                  disabled={sending || !input.trim() || !currentChat}
                  className="p-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-50 transition-all shadow-lg shadow-indigo-600/20"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
          <div className="max-w-4xl mx-auto mt-2 flex justify-between items-center px-1">
             <div className="text-[10px] text-slate-500 flex items-center">
                <Shield className="w-3 h-3 mr-1 text-emerald-500/50" /> Secure Semantic Enclave Active
             </div>
             {showMemories ? (
                <button onClick={() => setShowMemories(false)} className="text-[10px] text-indigo-400 hover:text-indigo-300">Hide Retrieval Context</button>
             ) : retrievedMemories.length > 0 && (
                <button onClick={() => setShowMemories(true)} className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center">
                  <BarChart2 className="w-3 h-3 mr-1" /> View Retrieved Memories ({retrievedMemories.length})
                </button>
             )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Shield({ className }: { className?: string }) {
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      width="24" 
      height="24" 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />
    </svg>
  );
}
