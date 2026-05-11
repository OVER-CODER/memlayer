# API Documentation

Complete reference for all MemLayer endpoints and usage patterns.

## Base URL

```
http://localhost:8000
```

## Authentication

No authentication required for MVP (single-user local setup).

## Response Format

All responses are JSON.

### Success Response

```json
{
  "data": { ... },
  "status": "success"
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status": "error"
}
```

---

## Workspaces

### Create Workspace

Creates a new workspace.

**POST** `/api/workspaces`

**Query Parameters:**
- `name` (string, required) - Workspace name
- `description` (string, optional) - Workspace description

**Example:**
```bash
curl -X POST "http://localhost:8000/api/workspaces?name=My%20Workspace&description=Testing%20memories"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Workspace",
  "description": "Testing memories",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

### List Workspaces

Lists all workspaces with pagination.

**GET** `/api/workspaces`

**Query Parameters:**
- `limit` (integer, default: 100) - Number of workspaces to return
- `offset` (integer, default: 0) - Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/workspaces?limit=50&offset=0"
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Workspace",
    "description": "Testing memories",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
]
```

---

### Get Workspace

Retrieves a specific workspace.

**GET** `/api/workspaces/{workspace_id}`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Example:**
```bash
curl "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "My Workspace",
  "description": "Testing memories",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

### Delete Workspace

Deletes a workspace and all associated data.

**DELETE** `/api/workspaces/{workspace_id}`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000"
```

**Response:**
```json
{
  "message": "Workspace deleted"
}
```

---

## Chats

### Create Chat

Creates a new chat in a workspace.

**POST** `/api/workspaces/{workspace_id}/chats`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Query Parameters:**
- `title` (string, optional) - Chat title

**Example:**
```bash
curl -X POST "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/chats?title=Conversation%201"
```

**Response:**
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Conversation 1",
  "created_at": "2024-01-01T12:00:00",
  "updated_at": "2024-01-01T12:00:00"
}
```

---

### List Chats

Lists all chats in a workspace.

**GET** `/api/workspaces/{workspace_id}/chats`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Query Parameters:**
- `limit` (integer, default: 50) - Number of chats
- `offset` (integer, default: 0) - Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/chats"
```

**Response:**
```json
[
  {
    "id": "650e8400-e29b-41d4-a716-446655440000",
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Conversation 1",
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
]
```

---

## Messages & Queries

### Query Chat (Main Pipeline)

Sends a message through the complete semantic memory pipeline.

**POST** `/api/chats/{chat_id}/query`

**Path Parameters:**
- `chat_id` (string) - Chat ID

**Request Body:**
```json
{
  "query": "What did we discuss about AI?",
  "top_k_memories": 5,
  "similarity_threshold": 0.3
}
```

**Response:**
```json
{
  "message_id": "750e8400-e29b-41d4-a716-446655440000",
  "response": "Based on our previous conversation, we discussed...",
  "retrieved_memories": [
    {
      "id": "mem-001",
      "content": "We were discussing machine learning...",
      "summary": "Discussion about ML basics",
      "source_type": "user_message",
      "similarity_score": 0.85,
      "importance_score": 0.7,
      "timestamp": "2024-01-01T10:00:00"
    }
  ],
  "context_metadata": {
    "total_memories_used": 3,
    "recent_messages_included": 5,
    "estimated_tokens": 450
  }
}
```

**Pipeline Steps (behind the scenes):**
1. User message is embedded (locally)
2. Semantic search finds top-k similar memories
3. Context is compiled from memories + chat history
4. Gemini API generates response
5. Response is stored as new memory

---

### Get Chat Messages

Retrieves all messages from a chat.

**GET** `/api/chats/{chat_id}/messages`

**Path Parameters:**
- `chat_id` (string) - Chat ID

**Query Parameters:**
- `limit` (integer, default: 50) - Number of messages

**Example:**
```bash
curl "http://localhost:8000/api/chats/650e8400-e29b-41d4-a716-446655440000/messages?limit=50"
```

**Response:**
```json
[
  {
    "id": "msg-001",
    "chat_id": "650e8400-e29b-41d4-a716-446655440000",
    "role": "user",
    "content": "What did we discuss?",
    "created_at": "2024-01-01T12:00:00"
  },
  {
    "id": "msg-002",
    "chat_id": "650e8400-e29b-41d4-a716-446655440000",
    "role": "assistant",
    "content": "We discussed...",
    "created_at": "2024-01-01T12:01:00"
  }
]
```

---

## Memories

### Create Memory

Manually create a memory object.

**POST** `/api/workspaces/{workspace_id}/memories`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Request Body:**
```json
{
  "raw_content": "Important information to remember",
  "source_type": "file_upload",
  "summary": "Key facts",
  "importance_score": 0.8,
  "metadata": {
    "file_name": "document.pdf",
    "topic": "AI"
  }
}
```

**Response:**
```json
{
  "id": "mem-001",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_type": "file_upload",
  "raw_content": "Important information to remember",
  "summary": "Key facts",
  "importance_score": 0.8,
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {
    "file_name": "document.pdf",
    "topic": "AI"
  }
}
```

---

### List Memories

Lists all memories in a workspace.

**GET** `/api/workspaces/{workspace_id}/memories`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Query Parameters:**
- `limit` (integer, default: 100) - Number of memories
- `offset` (integer, default: 0) - Pagination offset

**Example:**
```bash
curl "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/memories?limit=50"
```

**Response:**
```json
[
  {
    "id": "mem-001",
    "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
    "source_type": "user_message",
    "raw_content": "Tell me about AI",
    "summary": "User asking about AI",
    "importance_score": 0.6,
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

---

### Search Memories (Semantic)

Search for semantically similar memories.

**GET** `/api/workspaces/{workspace_id}/memories/search`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Query Parameters:**
- `query` (string, required) - Search query
- `top_k` (integer, default: 5) - Number of results
- `similarity_threshold` (float, default: 0.3) - Minimum similarity

**Example:**
```bash
curl "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/memories/search?query=machine%20learning&top_k=5"
```

**Response:**
```json
[
  {
    "id": "mem-001",
    "content": "Machine learning is a subset of AI...",
    "summary": "ML explanation",
    "source_type": "assistant_response",
    "similarity_score": 0.92,
    "importance_score": 0.7,
    "timestamp": "2024-01-01T11:00:00"
  }
]
```

---

### Get Memory

Retrieve a specific memory by ID.

**GET** `/api/workspaces/{workspace_id}/memories/{memory_id}`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID
- `memory_id` (string) - Memory ID

**Example:**
```bash
curl "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/memories/mem-001"
```

**Response:**
```json
{
  "id": "mem-001",
  "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_type": "user_message",
  "raw_content": "Tell me about AI",
  "summary": "User asking about AI",
  "importance_score": 0.6,
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {}
}
```

---

### Delete Memory

Delete a memory.

**DELETE** `/api/workspaces/{workspace_id}/memories/{memory_id}`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID
- `memory_id` (string) - Memory ID

**Example:**
```bash
curl -X DELETE "http://localhost:8000/api/workspaces/550e8400-e29b-41d4-a716-446655440000/memories/mem-001"
```

**Response:**
```json
{
  "message": "Memory deleted"
}
```

---

## Analytics

### Get Memory Statistics

Retrieves statistics about memories in a workspace.

**GET** `/api/workspaces/{workspace_id}/memories/stats/memories`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Response:**
```json
{
  "total_memories": 42,
  "by_source": {
    "user_message": 20,
    "assistant_response": 22
  },
  "avg_importance": 0.65,
  "oldest_memory": "2024-01-01T10:00:00",
  "newest_memory": "2024-01-01T15:30:00"
}
```

---

### Get Retrieval Statistics

Retrieves statistics about memory retrievals.

**GET** `/api/workspaces/{workspace_id}/memories/stats/retrievals`

**Path Parameters:**
- `workspace_id` (string) - Workspace ID

**Response:**
```json
{
  "total_retrievals": 15,
  "avg_similarity": 0.72,
  "max_similarity": 0.98,
  "min_similarity": 0.35
}
```

---

## System

### Health Check

Verifies backend is running.

**GET** `/health`

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

### Get Configuration

Retrieves system configuration.

**GET** `/api/config`

**Response:**
```json
{
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dim": 384,
  "gemini_model": "gemini-pro",
  "top_k_memories": 5,
  "memory_retrieval_threshold": 0.3
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 404 | Not found |
| 500 | Server error |

---

## Rate Limiting

No rate limiting in MVP.

---

## Batch Operations

For batch operations, call endpoints multiple times. In future versions:

- Memory creation batches
- Multi-query semantic search
- Bulk analytics

---

## WebSocket (Future)

Real-time streaming responses not implemented in MVP.

---

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Create workspace
ws_response = requests.post(
    f"{BASE_URL}/api/workspaces",
    params={"name": "My Workspace"}
)
workspace_id = ws_response.json()["id"]

# Create chat
chat_response = requests.post(
    f"{BASE_URL}/api/workspaces/{workspace_id}/chats",
    params={"title": "Chat 1"}
)
chat_id = chat_response.json()["id"]

# Send query
query_response = requests.post(
    f"{BASE_URL}/api/chats/{chat_id}/query",
    json={
        "query": "What is machine learning?",
        "top_k_memories": 5
    }
)
result = query_response.json()
print(result["response"])
```

### JavaScript

```javascript
const BASE_URL = "http://localhost:8000";

// Create workspace
const wsRes = await fetch(`${BASE_URL}/api/workspaces?name=My%20Workspace`, {
  method: "POST"
});
const workspace = await wsRes.json();

// Create chat
const chatRes = await fetch(
  `${BASE_URL}/api/workspaces/${workspace.id}/chats?title=Chat%201`,
  { method: "POST" }
);
const chat = await chatRes.json();

// Send query
const queryRes = await fetch(`${BASE_URL}/api/chats/${chat.id}/query`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "What is machine learning?",
    top_k_memories: 5
  })
});
const result = await queryRes.json();
console.log(result.response);
```

---

## Pagination

Endpoints supporting pagination use:
- `limit` - Number of results
- `offset` - Number to skip

Example:
```bash
# Get items 10-20
?limit=10&offset=10
```

---

## Further Development

Future API enhancements:
- Bulk operations
- WebSocket streaming
- GraphQL support
- Multi-model LLM selection
- Memory pruning/compression
- Advanced filtering
