import axios from 'axios';

export const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  console: {
    getWorkspaces: () => apiClient.get('/console/workspaces').then(res => res.data),
    getWorkspaceDiagnostics: (id: string) => apiClient.get(`/console/workspaces/${id}/diagnostics`).then(res => res.data),
    coordinate: (id: string, query: string) => apiClient.post(`/console/workspaces/${id}/coordinate`, { query }).then(res => res.data),
    getTelemetry: () => apiClient.get('/console/telemetry').then(res => res.data),
    getDiagnostics: () => apiClient.get('/console/diagnostics').then(res => res.data),
    getAuditTrail: () => apiClient.get('/console/governance/audit-trail').then(res => res.data),
    getGovernanceHealth: () => apiClient.get('/console/governance/health').then(res => res.data),
    getPolicyDecisions: () => apiClient.get('/console/governance/policy').then(res => res.data),
    getLineage: (id?: string) => apiClient.get('/console/governance/lineage', { params: { workspace_id: id } }).then(res => res.data),
    seedMockData: () => apiClient.post('/console/seed-mock-data').then(res => res.data),
  }
};

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
