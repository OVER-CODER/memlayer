# MemLayer - Persistent AI Memory Runtime

MVP foundation for a startup building persistent AI workspaces with shared semantic memory.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Next.js Frontend                       │
│          (Workspace List, Chat, Memory Inspector)       │
└─────────────┬───────────────────────────────────────────┘
              │ HTTP/REST API
              │
┌─────────────▼───────────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Chat Orchestration Service                      │  │
│  │  - Handles message pipeline                      │  │
│  │  - Coordinates all components                    │  │
│  └──────────────────────────────────────────────────┘  │
│                      │                                   │
│  ┌──────────────────┴──────────────────┬─────────────┐ │
│  │                 │                   │             │ │
│  ▼                 ▼                   ▼             ▼ │
│ Memory       Memory            Context            LLM  │
│ Storage      Retrieval       Compilation        Service│
│ Service      Service          Service                   │
│  │                 │                   │             │ │
│  └──────────────────┴───────────────────┴─────────────┘ │
│           │                                              │
│           ▼                                              │
│    Embedding Service (Model-Agnostic)                  │
│    - sentence-transformers (local)                     │
│    - Can extend to other providers                     │
└─────────────┬───────────────────────────────────────────┘
              │
┌─────────────┴───────────────────────────────────────────┐
│          PostgreSQL + pgvector                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ Tables:                                            │ │
│  │ - workspaces                                       │ │
│  │ - chats                                            │ │
│  │ - messages                                         │ │
│  │ - memories (with vector embedding)                │ │
│  │ - memory_retrievals (analytics)                   │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Memory Storage Service (`app/services/memory_storage.py`)
- Creates and persists semantic memory objects
- Generates embeddings for raw content
- Tracks memory metadata and importance scores

**Key Methods:**
- `create_memory()` - Store new memory with embedding
- `list_workspace_memories()` - Retrieve all memories for workspace
- `update_importance()` - Adjust memory importance dynamically

### 2. Memory Retrieval Service (`app/services/memory_retrieval.py`)
- Performs semantic search using pgvector
- Retrieves relevant memories for queries
- Applies importance weighting to results
- Logs retrievals for analytics

**Key Methods:**
- `retrieve()` - Get semantically similar memories
- `retrieve_batch()` - Retrieve for multiple queries
- `get_retrieval_stats()` - Analytics on retrieval performance

### 3. Context Compilation Service (`app/services/context_compilation.py`)
- Assembles comprehensive context from memories
- Includes recent chat history
- Compiles compressed prompts for LLM
- Token limit management

**Key Methods:**
- `compile_context()` - Build full contextual prompt
- Returns: workspace context, retrieved memories, chat history

### 4. LLM Service (`app/services/llm.py`)
- Abstract provider interface (extensible)
- Gemini API integration
- Future support for other LLMs

**Key Methods:**
- `generate()` - Direct LLM generation
- `generate_with_context()` - Context-aware generation

### 5. Chat Orchestration Service (`app/services/chat_orchestration.py`)
- Coordinates the complete message pipeline:
  1. Store user message
  2. Retrieve relevant memories
  3. Compile context
  4. Generate LLM response
  5. Store response in memory

### 6. Embedding Service (`app/services/embedding.py`)
- Model-agnostic embedding layer
- Local sentence-transformers support
- Future support for API-based embeddings

## Project Structure

```
memlayer-backend/
├── app/
│   ├── api/
│   │   ├── workspaces.py      # Workspace endpoints
│   │   ├── chats.py           # Chat endpoints
│   │   └── memories.py        # Memory endpoints
│   ├── core/
│   │   └── config.py          # Configuration
│   ├── db/
│   │   ├── models.py          # SQLAlchemy models
│   │   └── session.py         # Database setup
│   ├── services/
│   │   ├── embedding.py       # Embedding provider
│   │   ├── memory_storage.py  # Memory storage
│   │   ├── memory_retrieval.py# Memory retrieval
│   │   ├── context_compilation.py
│   │   ├── llm.py             # LLM service
│   │   ├── workspace.py       # Workspace management
│   │   └── chat_orchestration.py
│   ├── schemas/
│   │   └── memory.py          # Pydantic schemas
│   └── main.py                # FastAPI app
├── init_db.py                 # Database initialization
├── evaluate_locomo.py         # Dataset evaluation
├── pyproject.toml             # Poetry config
└── .env.example               # Environment template

memlayer-frontend/
├── app/
│   ├── layout.tsx             # Root layout
│   ├── page.tsx               # Workspace list
│   └── workspace/
│       └── [workspace_id]/
│           └── page.tsx       # Chat page
├── lib/
│   ├── api.ts                 # API client
│   └── store.ts               # Zustand store
├── types/
│   └── index.ts               # TypeScript types
├── styles/
│   └── globals.css            # Global styles
├── package.json
├── next.config.js
└── tsconfig.json
```

## Memory Object Format

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "source_type": "user_message|assistant_response|file_upload",
  "raw_content": "Text content",
  "summary": "Brief summary",
  "embedding": [0.12, 0.34, ...],  // 384-dimensional vector
  "timestamp": "2024-01-01T12:00:00",
  "importance_score": 0.7,           // 0-1 scale
  "metadata": {}
}
```

## API Routes

### Workspaces
- `POST /api/workspaces` - Create workspace
- `GET /api/workspaces` - List workspaces
- `GET /api/workspaces/{id}` - Get workspace
- `DELETE /api/workspaces/{id}` - Delete workspace

### Chats
- `POST /api/workspaces/{id}/chats` - Create chat
- `GET /api/workspaces/{id}/chats` - List chats
- `POST /api/chats/{id}/query` - Send message (full pipeline)
- `GET /api/chats/{id}/messages` - Get chat messages

### Memories
- `GET /api/workspaces/{id}/memories` - List memories
- `GET /api/workspaces/{id}/memories/search?query=...` - Search memories
- `POST /api/workspaces/{id}/memories` - Create memory
- `GET /api/workspaces/{id}/memories/stats/memories` - Memory stats
- `GET /api/workspaces/{id}/memories/stats/retrievals` - Retrieval stats

## Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Poetry (Python dependency manager)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd memlayer-backend

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
nano .env

# Initialize database (requires PostgreSQL running)
python init_db.py

# Run backend
poetry run python -m uvicorn app.main:app --reload
```

**Backend runs on:** http://localhost:8000

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd memlayer-frontend

# Install dependencies
npm install

# Create .env.local for API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run frontend
npm run dev
```

**Frontend runs on:** http://localhost:3000

## Message Processing Pipeline

When a user sends a message:

```
1. USER MESSAGE
   ↓
2. Store user message in messages table
   ↓
3. Create memory from user message
   ↓
4. EMBED & RETRIEVE
   - Embed user query
   - Semantic search in pgvector
   - Get top-5 similar memories
   ↓
5. COMPILE CONTEXT
   - Workspace context
   - Retrieved memories
   - Recent chat history
   ↓
6. LLM GENERATION
   - Send compiled prompt to Gemini
   - Get response
   ↓
7. STORE & RETURN
   - Store assistant message
   - Store response as memory
   - Return memories used + response
```

## Configuration

Key settings in `app/core/config.py`:

```python
embedding_model = "all-MiniLM-L6-v2"  # Local model
embedding_dim = 384                    # Vector dimension
top_k_memories = 5                     # Default retrieval count
memory_retrieval_threshold = 0.3       # Similarity threshold
gemini_model = "gemini-pro"            # LLM model
```

## Extensibility Points

### 1. Add New Embedding Provider
```python
class MyEmbeddingProvider(EmbeddingProvider):
    def embed(self, text):
        # Your implementation
        pass
    
    def get_dimension(self):
        return 768
```

### 2. Add New LLM Provider
```python
class MyLLMProvider(LLMProvider):
    def generate(self, prompt, **kwargs):
        # Your implementation
        pass
```

### 3. Extend Memory with Custom Metadata
```python
memory = memory_service.create_memory(
    workspace_id=ws_id,
    raw_content="text",
    metadata={
        "source_file": "document.pdf",
        "topic": "machine-learning",
        "confidence": 0.95
    }
)
```

## Evaluation

Run LOCOMO dataset evaluation:

```bash
cd memlayer-backend
poetry run python evaluate_locomo.py
```

Outputs evaluation metrics:
- Recall@1, Recall@5
- Mean Reciprocal Rank
- Performance by question category
- Retrieval statistics

## Key Architectural Decisions

### 1. Model-Agnostic Layers
- Memory system doesn't depend on specific LLM
- Embedding provider is pluggable
- Easy to swap backends

### 2. Local Embeddings
- Use sentence-transformers for privacy
- Can embed entire corpus locally
- No API rate limits

### 3. PostgreSQL + pgvector
- Vector similarity search native to database
- Efficient indexing (IVFFLAT)
- SQL-based retrieval logic

### 4. Importance Scoring
- Memories have mutable importance
- Combined with similarity for ranking
- Enables personalization

### 5. Comprehensive Logging
- Memory retrievals tracked
- Analytics on system performance
- Future basis for optimization

## Future Enhancements

NOT in this MVP:
- Multi-agent coordination
- Distributed systems
- Authentication/Authorization
- Advanced UI
- Production scaling
- Worker queues
- Kubernetes deployment

FOR FUTURE ITERATIONS:
- Support multiple LLM providers
- Agent-to-agent memory sharing
- Cross-session continuity
- Dynamic importance updating
- Memory compression
- Semantic memory hierarchies
- Graph-based memory relationships

## Development Workflow

1. **Backend Changes**
   - Modify service in `app/services/`
   - Update schema in `app/schemas/`
   - Add route in `app/api/`
   - Test with:
     ```bash
     poetry run pytest tests/
     ```

2. **Frontend Changes**
   - Update component in `components/`
   - Update API client in `lib/api.ts`
   - Test on http://localhost:3000

3. **Database Changes**
   - Modify models in `app/db/models.py`
   - Run `python init_db.py` to recreate

4. **Commits**
   - Atomic commits per feature
   - Clear commit messages
   - Reference architecture decisions

## Testing

```bash
# Backend tests
cd memlayer-backend
poetry run pytest tests/ -v

# Frontend tests
cd memlayer-frontend
npm run test
```

## Troubleshooting

### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
pg_isready

# Create database manually
createdb memlayer_dev

# Create pgvector extension
psql memlayer_dev -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Backend Import Errors
```bash
cd memlayer-backend
poetry install
poetry update
```

### Frontend API Connection Issues
- Verify backend is running on http://localhost:8000
- Check NEXT_PUBLIC_API_URL in .env.local
- Check CORS settings in app/main.py

## Resources

- [Sentence Transformers](https://www.sbert.net/)
- [pgvector](https://github.com/pgvector/pgvector)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [LOCOMO Dataset](https://github.com/qipeng/LOCOMO)

## License

MIT
