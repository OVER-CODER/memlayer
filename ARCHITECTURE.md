# Architecture & Configuration Reference

## System Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT BROWSER                                   │
│                         http://localhost:3000                              │
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │ HTTP/JSON
                             │
┌────────────────────────────▼─────────────────────────────────────────────────┐
│                       NEXT.JS FRONTEND                                       │
│                   (TypeScript + Tailwind)                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │  Workspace Page     │  │  Chat Page       │  │  Memory Inspector    │  │
│  │  - List workspaces  │  │  - Send messages │  │  - Search memories   │  │
│  │  - Create/Delete    │  │  - View history  │  │  - View stats        │  │
│  │  - Navigate         │  │  - Real-time UI  │  │  - Manage memories   │  │
│  └─────────────────────┘  └──────────────────┘  └──────────────────────┘  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      API Client (axios)                             │   │
│  │  - workspacesAPI    - chatsAPI    - memoriesAPI                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Global State (Zustand)                           │   │
│  │  - currentWorkspace, currentChat, memories, loading, error         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└────────────────────────────┬─────────────────────────────────────────────────┘
                             │ REST API
                             │ POST/GET/DELETE
                             │
┌────────────────────────────▼─────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                                        │
│                   (Python + SQLAlchemy)                                      │
│                  http://localhost:8000                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        API Routes Layer                              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────────────┐ │   │
│  │  │ Workspaces │  │   Chats    │  │         Memories               │ │   │
│  │  │            │  │            │  │  - POST create                │ │   │
│  │  │ - POST     │  │ - POST     │  │  - GET list/search            │ │   │
│  │  │ - GET      │  │ - GET      │  │  - GET search (semantic)      │ │   │
│  │  │ - DELETE   │  │ - DELETE   │  │  - DELETE                     │ │   │
│  │  │            │  │            │  │  - Stats endpoints            │ │   │
│  │  │            │  │ - POST /query (MAIN PIPELINE)                  │ │   │
│  │  └────────────┘  └────────────┘  └────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                  Chat Orchestration Service                          │   │
│  │  (Coordinates the complete message processing pipeline)             │   │
│  │                                                                      │   │
│  │  1. Store user message                                              │   │
│  │  2. Create memory from message                                      │   │
│  │  3. ↓ Call Memory Retrieval Service                                 │   │
│  │  4. ↓ Call Context Compilation Service                              │   │
│  │  5. ↓ Call LLM Service                                              │   │
│  │  6. Store response as memory                                        │   │
│  │  7. Return results to client                                        │   │
│  │                                                                      │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                    │                │                │                      │
├────────────────────┼────────────────┼────────────────┼─────────────────────┤
│                    │                │                │                      │
│  ┌──────────────┐  │   ┌──────────────────┐    ┌──────────────┐            │
│  │ Memory       │  │   │ Memory Retrieval │    │ Context      │            │
│  │ Storage      │  │   │ Service          │    │ Compilation  │            │
│  │              │  │   │                  │    │              │            │
│  │ - embed()    │  │   │ - retrieve()     │    │ - compile()  │            │
│  │ - create()   │  │   │ - batch_retrieve │    │ - assemble() │            │
│  │ - update()   │  │   │ - get_stats()    │    │              │            │
│  │              │  │   │                  │    │              │            │
│  └──────────────┘  │   └──────────────────┘    └──────────────┘            │
│                    │                │                │                      │
├────────┬───────────┴────────────────┼────────────────┴──────────────────────┤
│        │                           │                                        │
│  ┌─────▼──────────────────────────┐│  ┌──────────────────────────────────┐ │
│  │    Embedding Service           ││  │    LLM Service                   │ │
│  │  (Model-agnostic)             ││  │  (Model-agnostic)               │ │
│  │                                ││  │                                  │ │
│  │ ┌─ SentenceTransformers       ││  │ ┌─ Gemini Provider               │ │
│  │ │  Provider (LOCAL)           ││  │ │  (Gemini API)                  │ │
│  │ │                             ││  │ │  - generate()                  │ │
│  │ │ - embed()                   ││  │ │  - generate_with_context()    │ │
│  │ │ - embed_batch()             ││  │ │                                │ │
│  │ │ - get_dimension()           ││  │ │ Can extend with:               │ │
│  │ │                             ││  │ │ - OpenAI Provider              │ │
│  │ │ Can extend with:            ││  │ │ - Claude Provider              │ │
│  │ │ - OpenAI Provider          ││  │ │ - Local LLM Provider           │ │
│  │ │ - Google Provider          ││  │ │                                │ │
│  │ │ - Cohere Provider          ││  │ └────────────────────────────────┘ │
│  │ └────────────────────────────┘│  │                                     │ │
│  └──────────────────────────────┘│  └────────────────────────────────────┘ │
│                                  │                                         │
└──────────────────────────────────┼─────────────────────────────────────────┘
                                   │ SQL Queries
                                   │
┌──────────────────────────────────▼─────────────────────────────────────────┐
│                 POSTGRESQL + PGVECTOR                                       │
│                    http://localhost:5432                                    │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐│
│  │ workspaces       │  │ chats            │  │ messages                 ││
│  │ ─────────────────│  │ ─────────────────│  │ ──────────────────────────│
│  │ id (PK)          │  │ id (PK)          │  │ id (PK)                  ││
│  │ name             │  │ workspace_id (FK)│  │ chat_id (FK)             ││
│  │ description      │  │ title            │  │ role (user/assistant)    ││
│  │ created_at       │  │ created_at       │  │ content                  ││
│  │ updated_at       │  │ updated_at       │  │ created_at               ││
│  │                  │  │                  │  │                          ││
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘│
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ memories (CORE TABLE WITH VECTOR INDEX)                            │ │
│  │ ────────────────────────────────────────────────────────────────    │ │
│  │ id (PK)                                                             │ │
│  │ workspace_id (FK)                                                   │ │
│  │ source_type (user_message, assistant_response, file_upload)        │ │
│  │ raw_content (TEXT)                                                  │ │
│  │ summary (TEXT)                                                      │ │
│  │ embedding (Vector<384>)  ← INDEXED with IVFFLAT                   │ │
│  │ timestamp (indexed for sorting)                                     │ │
│  │ importance_score (0-1)                                              │ │
│  │ metadata (JSON)                                                     │ │
│  │                                                                     │ │
│  │ Queries:                                                            │ │
│  │ - Cosine similarity: SELECT * WHERE embedding <=> query_vec       │ │
│  │ - Fast retrieval: Index prevents full table scan                  │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐│
│  │ memory_retrievals (ANALYTICS)                                        ││
│  │ ──────────────────────────────────                                   ││
│  │ id (PK)                                                              ││
│  │ workspace_id (FK)                                                    ││
│  │ query (TEXT)                                                         ││
│  │ retrieved_memory_ids (JSON array)                                    ││
│  │ similarity_scores (JSON array)                                       ││
│  │ timestamp                                                            ││
│  │                                                                      ││
│  │ Used for analytics and optimization                                 ││
│  └──────────────────────────────────────────────────────────────────────┘│
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Message Processing Pipeline

```
User Types: "What did we discuss about AI?"
│
├─► STEP 1: STORE MESSAGE
│   └─► Save to messages table
│       └─► Save to memories table with importance_score=0.6
│
├─► STEP 2: EMBEDDING
│   └─► Memory Retrieval Service calls Embedding Service
│       └─► SentenceTransformers generates 384-d vector locally
│           └─► query_embedding = [0.12, -0.45, 0.78, ...]
│
├─► STEP 3: SEMANTIC SEARCH (pgvector)
│   └─► Query: SELECT * FROM memories
│           WHERE workspace_id = ?
│           ORDER BY embedding <=> query_vector
│           LIMIT 5
│       └─► Retrieved memories:
│           1. "We discussed ML basics" (sim: 0.92)
│           2. "AI overview" (sim: 0.85)
│           3. "Deep learning intro" (sim: 0.78)
│
├─► STEP 4: CONTEXT COMPILATION
│   └─► Assemble:
│       ├─► Workspace context
│       ├─► Retrieved memories (3 items)
│       ├─► Recent chat history (last 5 messages)
│       └─► Compiled prompt (max 2000 tokens):
│           "# Context
│            We previously discussed machine learning basics...
│            
│            # Current Query
│            What did we discuss about AI?"
│
├─► STEP 5: LLM GENERATION
│   └─► LLM Service calls Gemini API
│       └─► POST https://api.gemini.google/v1/chat
│           Prompt: [compiled context above]
│           └─► Response: "Based on our discussion, we covered..."
│
├─► STEP 6: STORE RESPONSE
│   └─► Save to messages table (role=assistant)
│       └─► Create memory (source_type=assistant_response)
│           └─► Generate embedding for response
│               └─► Store in memories table
│
├─► STEP 7: LOG RETRIEVAL
│   └─► Save to memory_retrievals table
│       └─► Query text, retrieved IDs, similarity scores
│           └─► For future analytics
│
└─► STEP 8: RETURN TO CLIENT
    └─► {
         "response": "Based on our discussion...",
         "retrieved_memories": [...],
         "context_metadata": {...}
        }
```

## Component Interactions

### Service Call Graph

```
FastAPI Route: POST /api/chats/{chat_id}/query
    │
    └─► ChatOrchestrationService.process_message()
         │
         ├─► Store message in DB
         │
         ├─► MemoryStorageService.create_memory()
         │   └─► EmbeddingService.embed() → pgvector stores it
         │
         ├─► MemoryRetrievalService.retrieve()
         │   ├─► EmbeddingService.embed(query)
         │   ├─► SQL query with pgvector
         │   └─► Return top-k memories with scores
         │
         ├─► ContextCompilationService.compile_context()
         │   ├─► Get workspace context
         │   ├─► Format retrieved memories
         │   ├─► Get recent chat messages
         │   └─► Assemble final prompt
         │
         ├─► LLMService.generate_with_context()
         │   ├─► GeminiProvider.generate()
         │   └─► Call Gemini API
         │
         ├─► MemoryStorageService.create_memory() [response]
         │   └─► Store response as new memory
         │
         └─► Return results to client
```

## Configuration Schema

### Backend (.env)

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost/memlayer_dev

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2    # sentence-transformers model
EMBEDDING_DIM=384                    # Vector dimension

# LLM Configuration
GEMINI_API_KEY=your_api_key_here    # Required for LLM service
GEMINI_MODEL=gemini-pro             # Which model to use

# Memory Configuration
TOP_K_MEMORIES=5                    # Default retrieval count
MEMORY_RETRIEVAL_THRESHOLD=0.3      # Min similarity score
MEMORY_CHUNK_SIZE=500               # Chars per memory object

# Server Configuration
DEBUG=true                          # Enable debug mode
LOG_LEVEL=INFO                      # Logging level
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Extension Points

### 1. Add New Embedding Provider

**Location**: `app/services/embedding.py`

```python
class CustomEmbeddingProvider(EmbeddingProvider):
    def embed(self, text):
        # Your implementation
        pass
    
    def get_dimension(self):
        return 768
```

**Register**:
```python
from app.services.embedding import EmbeddingService, CustomEmbeddingProvider
service = EmbeddingService(CustomEmbeddingProvider())
```

### 2. Add New LLM Provider

**Location**: `app/services/llm.py`

```python
class CustomLLMProvider(LLMProvider):
    def generate(self, prompt, **kwargs):
        # Your implementation
        pass
```

**Register**:
```python
from app.services.llm import LLMService, CustomLLMProvider
service = LLMService(CustomLLMProvider())
```

### 3. Add New API Endpoint

**Location**: `app/api/` (create new file)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter(prefix="/api/custom", tags=["custom"])

@router.get("")
def custom_endpoint(db: Session = Depends(get_db)):
    # Your logic
    return {"result": "success"}

# In app/main.py, add:
# app.include_router(custom.router)
```

### 4. Add New Memory Metadata

**Location**: `app/db/models.py`

```python
class Memory(Base):
    # ... existing fields ...
    custom_field = Column(String, nullable=True)
    
    # Or use JSON metadata
    metadata = Column(JSON, default={}, nullable=True)
```

**Update schemas** in `app/schemas/memory.py` to include new field.

## Performance Tuning

### Database Optimization

```sql
-- Create indices for common queries
CREATE INDEX idx_memory_workspace ON memories(workspace_id);
CREATE INDEX idx_memory_timestamp ON memories(timestamp DESC);
CREATE INDEX idx_memory_importance ON memories(importance_score DESC);

-- Vector index (auto-created by init_db.py)
CREATE INDEX idx_memories_embedding ON memories 
    USING ivfflat (embedding vector_cosine_ops) 
    WITH (lists = 100);

-- Maintenance
ANALYZE memories;
REINDEX INDEX idx_memories_embedding;
```

### Backend Optimization

```python
# Batch embeddings for performance
embeddings = embedding_service.embed_batch(texts, batch_size=64)

# Cache embeddings to avoid recomputation
from functools import lru_cache

@lru_cache(maxsize=10000)
def get_cached_embedding(text):
    return embedding_service.embed(text)

# Use connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
)
```

### Frontend Optimization

```typescript
// Memoize components
const MemoizedMemoryVisualizer = memo(MemoryVisualizer);

// Lazy load pages
import dynamic from 'next/dynamic';
const MemoryInspector = dynamic(() => import('./MemoryInspector'));

// Debounce search
const debouncedSearch = debounce(handleSearch, 300);
```

## Monitoring & Observability

### Key Metrics to Track

```python
# Retrieval metrics
- avg_similarity_score per query
- retrieval_latency (pgvector search time)
- memories_per_workspace (growth over time)

# LLM metrics
- llm_generation_time
- llm_token_count
- llm_error_rate

# System metrics
- embedding_generation_time
- database_query_time
- api_response_time
- memory_usage
```

### Logging Setup

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

**Diagram updated**: 2024  
**Last reviewed**: MVP v0.1.0
