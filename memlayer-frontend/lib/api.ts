import axios, { AxiosInstance } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Workspace API
export const workspacesAPI = {
  create: (name: string, description?: string) =>
    apiClient.post('/api/workspaces', { name, description }),
  
  list: (limit?: number, offset?: number) =>
    apiClient.get('/api/workspaces', { params: { limit, offset } }),
  
  get: (id: string) =>
    apiClient.get(`/api/workspaces/${id}`),
  
  delete: (id: string) =>
    apiClient.delete(`/api/workspaces/${id}`),
};

// Chat API
export const chatsAPI = {
  create: (workspaceId: string, title?: string) =>
    apiClient.post(`/api/workspaces/${workspaceId}/chats`, { title }),
  
  list: (workspaceId: string, limit?: number, offset?: number) =>
    apiClient.get(`/api/workspaces/${workspaceId}/chats`, { params: { limit, offset } }),
  
  get: (chatId: string) =>
    apiClient.get(`/api/chats/${chatId}`),
  
  query: (chatId: string, query: string, topK?: number) =>
    apiClient.post(`/api/chats/${chatId}/query`, { query, top_k_memories: topK }),
  
  getMessages: (chatId: string, limit?: number) =>
    apiClient.get(`/api/chats/${chatId}/messages`, { params: { limit } }),
};

// Memory API
export const memoriesAPI = {
  create: (workspaceId: string, rawContent: string, sourceType?: string) =>
    apiClient.post(`/api/workspaces/${workspaceId}/memories`, { 
      raw_content: rawContent, 
      source_type: sourceType 
    }),
  
  list: (workspaceId: string, limit?: number, offset?: number) =>
    apiClient.get(`/api/workspaces/${workspaceId}/memories`, { params: { limit, offset } }),
  
  search: (workspaceId: string, query: string, topK?: number) =>
    apiClient.get(`/api/workspaces/${workspaceId}/memories/search`, { 
      params: { query, top_k: topK } 
    }),
  
  get: (workspaceId: string, memoryId: string) =>
    apiClient.get(`/api/workspaces/${workspaceId}/memories/${memoryId}`),
  
  delete: (workspaceId: string, memoryId: string) =>
    apiClient.delete(`/api/workspaces/${workspaceId}/memories/${memoryId}`),
  
  getStats: (workspaceId: string) =>
    apiClient.get(`/api/workspaces/${workspaceId}/memories/stats/memories`),
  
  getRetrievalStats: (workspaceId: string) =>
    apiClient.get(`/api/workspaces/${workspaceId}/memories/stats/retrievals`),
};

export default apiClient;
