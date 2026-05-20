export interface Workspace {
  id: string;
  workspace_id?: string; // For Console API compatibility
  name: string;
  description?: string;
  provider?: string;
  token_budget?: number;
  memory_count?: number;
  created_at: string;
  updated_at: string;
}

export interface Chat {
  id: string;
  workspace_id: string;
  title?: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  chat_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface Memory {
  id: string;
  workspace_id: string;
  source_type: string;
  raw_content: string;
  summary?: string;
  importance_score: number;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface RetrievedMemory {
  id: string;
  content: string;
  summary?: string;
  source_type: string;
  similarity_score: number;
  importance_score: number;
  timestamp: string;
}

export interface ChatQueryResponse {
  message_id: string;
  response: string;
  retrieved_memories: RetrievedMemory[];
  context_metadata: {
    total_memories_used: number;
    recent_messages_included: number;
    estimated_tokens: number;
  };
}

export interface MemoryStats {
  total_memories: number;
  by_source: Record<string, number>;
  avg_importance: number;
  oldest_memory?: string;
  newest_memory?: string;
}
