# MemLayer Documentation Index

Welcome to MemLayer! This is a **foundational memory runtime for persistent AI workspaces**. Start here to understand the project and get started.

## 📚 Documentation Map

### Getting Started
1. **[QUICKSTART.md](./QUICKSTART.md)** ⭐ **START HERE**
   - 5-minute setup guide
   - Verification steps
   - Troubleshooting

2. **[README.md](./README.md)**
   - Complete architecture overview
   - Component descriptions
   - Message processing pipeline
   - Project structure

### Understanding the System
3. **[ARCHITECTURE.md](./ARCHITECTURE.md)**
   - System architecture diagrams (ASCII)
   - Data flow visualizations
   - Component interactions
   - Configuration schema
   - Performance tuning

4. **[SUMMARY.md](./SUMMARY.md)**
   - Executive overview
   - Key features
   - Design decisions
   - What was built

### Using MemLayer
5. **[API.md](./API.md)**
   - Complete endpoint reference
   - Request/response examples
   - Code examples (Python/JS)
   - Error codes

### Extending MemLayer
6. **[DEVELOPMENT.md](./DEVELOPMENT.md)**
   - Adding new LLM providers
   - Adding embedding providers
   - File upload support
   - Memory compression
   - Testing strategies

### Verification
7. **[CHECKLIST.md](./CHECKLIST.md)**
   - Implementation status
   - Testing checklist
   - Code quality metrics
   - Success criteria

---

## 🚀 Quick Navigation

### "I just cloned the repo"
→ Read [QUICKSTART.md](./QUICKSTART.md) (10 minutes)

### "I want to understand how it works"
→ Read [README.md](./README.md) + [ARCHITECTURE.md](./ARCHITECTURE.md) (30 minutes)

### "I want to use the API"
→ Read [API.md](./API.md) and try examples (20 minutes)

### "I want to extend the system"
→ Read [DEVELOPMENT.md](./DEVELOPMENT.md) (45 minutes)

### "I want to verify completeness"
→ Check [CHECKLIST.md](./CHECKLIST.md) and [SUMMARY.md](./SUMMARY.md) (15 minutes)

---

## 🎯 Key Concepts

### Memory Object
Every piece of information stored in the system:
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "source_type": "user_message|assistant_response|file_upload",
  "raw_content": "The actual text/content",
  "summary": "Brief summary",
  "embedding": [0.12, 0.34, ...],  // 384-dimensional vector
  "importance_score": 0.7,          // 0-1 scale
  "timestamp": "2024-01-01T12:00:00"
}
```

### Message Processing Pipeline
When a user sends a message:
1. **Embed** the query locally (sentence-transformers)
2. **Retrieve** relevant memories (pgvector semantic search)
3. **Compile** context from memories + chat history
4. **Generate** response (Gemini API)
5. **Store** response as new memory

### Services (Modular Components)
- **MemoryStorageService**: Persist and retrieve memories
- **MemoryRetrievalService**: Semantic search with pgvector
- **ContextCompilationService**: Assemble prompts from context
- **EmbeddingService**: Generate vectors locally
- **LLMService**: Interface with Gemini (or other LLMs)
- **ChatOrchestrationService**: Coordinates the pipeline
- **WorkspaceService**: Workspace and chat management

---

## 📁 Project Structure

```
memlayer/
├── memlayer-backend/              # FastAPI backend
│   ├── app/
│   │   ├── services/              # Core business logic (7 services)
│   │   ├── api/                   # REST endpoints (3 route files)
│   │   ├── db/                    # Database (models, session)
│   │   ├── core/                  # Configuration
│   │   └── schemas/               # Pydantic models
│   ├── evaluate_locomo.py         # Dataset evaluation
│   ├── init_db.py                 # Database setup
│   └── pyproject.toml             # Dependencies
│
├── memlayer-frontend/             # Next.js frontend
│   ├── app/                       # Pages (workspace, chat, memories)
│   ├── components/                # React components
│   ├── lib/                       # API client, store, types
│   ├── styles/                    # Tailwind CSS
│   └── package.json               # Dependencies
│
├── Dataset/                       # LOCOMO dataset
├── Documentation/                 # This folder
│   ├── README.md                  # Architecture
│   ├── QUICKSTART.md              # Setup
│   ├── API.md                     # Endpoints
│   ├── ARCHITECTURE.md            # Diagrams
│   ├── DEVELOPMENT.md             # Extensions
│   ├── SUMMARY.md                 # Overview
│   ├── CHECKLIST.md               # Verification
│   └── INDEX.md                   # This file
└── .env.example                   # Configuration template
```

---

## 🔧 Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM for database operations
- **PostgreSQL**: Primary database
- **pgvector**: PostgreSQL vector extension
- **sentence-transformers**: Local embeddings
- **google-generativeai**: Gemini API client

### Frontend
- **Next.js 14**: React framework
- **TypeScript**: Type safety
- **Tailwind CSS**: Styling
- **Zustand**: State management
- **axios**: HTTP client

### Database
- **PostgreSQL 14+**: Required
- **pgvector**: Vector similarity search

---

## 📊 System Capabilities

### What It Can Do
✅ Persist conversations across sessions  
✅ Store semantic memories with embeddings  
✅ Retrieve relevant context using similarity search  
✅ Generate AI responses with context  
✅ Maintain conversation continuity  
✅ Visualize retrieved memories  
✅ Benchmark on LOCOMO dataset  
✅ Extend with new LLM/embedding providers  

### What It's NOT (MVP Scope)
❌ Multi-agent orchestration  
❌ Distributed systems  
❌ Authentication/multi-user  
❌ Production deployment  
❌ Queues/workers  
❌ Advanced UI features  
❌ Cloud deployment  

### Future Enhancements
🔜 File upload support  
🔜 Memory compression  
🔜 Multi-LLM support  
🔜 Memory categorization  
🔜 Advanced analytics  
🔜 Multi-agent memory sharing  

---

## 💡 Design Philosophy

### 1. Modularity Over Monoliths
Each service has a single responsibility and clear interface.

### 2. Extensibility By Design
Abstract providers for LLM and embeddings make it easy to swap implementations.

### 3. Local-First Privacy
Embeddings generated locally, no external APIs for core functionality.

### 4. SQL-Native
Vector operations in PostgreSQL, not a separate vector database.

### 5. Developer Experience
Clean code, comprehensive documentation, and examples for extending.

---

## 🧪 Testing & Evaluation

### LOCOMO Dataset
The system includes evaluation against the LOCOMO dataset:
- Long-context conversations
- Multiple question types
- Retrieval quality metrics

Run evaluation:
```bash
cd memlayer-backend
poetry run python evaluate_locomo.py
```

### Manual Testing
All endpoints can be tested with curl or the provided frontend UI.

### Code Quality
- Type hints throughout
- Docstrings on key functions
- Error handling on all APIs
- Structured logging capability

---

## 📈 Performance

### Latency (on local machine)
- Embedding generation: ~500ms (first load)
- Semantic search: ~50ms (pgvector)
- LLM generation: ~3-5s (Gemini)
- Context compilation: <10ms

### Throughput
- Can handle hundreds of memories
- Supports concurrent requests
- Batch operations ready

### Storage
- ~1KB per memory (content + embedding)
- 384-dimensional vectors optimized in pgvector

---

## 🚀 Deployment Paths

### Local Development
See QUICKSTART.md for local setup.

### Docker Deployment
```dockerfile
# Backend
FROM python:3.10
WORKDIR /app
COPY memlayer-backend .
RUN poetry install
CMD ["poetry", "run", "python", "-m", "uvicorn", "app.main:app"]

# Frontend
FROM node:18
WORKDIR /app
COPY memlayer-frontend .
RUN npm install && npm run build
CMD ["npm", "start"]
```

### Production Ready
- PostgreSQL with backups
- Environment-based configuration
- Logging to files
- Error tracking (future)
- Rate limiting (future)

---

## 🤝 Contributing

### Code Style
- Python: Black formatting, type hints
- TypeScript: ESLint, strict mode
- Database: SQL migrations

### Testing
- Add tests for new services
- Test API endpoints
- Verify database migrations

### Documentation
- Update docs for new features
- Add code comments on complex logic
- Include examples in DEVELOPMENT.md

---

## 📞 Support

### Common Issues

**Backend won't start**
→ Check DATABASE_URL in .env  
→ Verify PostgreSQL is running  
→ Run `python init_db.py`

**Frontend can't reach backend**
→ Verify NEXT_PUBLIC_API_URL in .env.local  
→ Check backend is running on 8000  

**API Key errors**
→ Verify GEMINI_API_KEY in .env  
→ Test key validity at Google AI Studio

See DEVELOPMENT.md for more troubleshooting.

---

## 📚 Learning Resources

### Understanding the System
1. Read README.md for architecture
2. Review ARCHITECTURE.md for diagrams
3. Study ChatOrchestrationService in code
4. Try API examples in API.md

### Extending the System
1. Review DEVELOPMENT.md
2. Look at existing service implementations
3. Follow abstraction patterns
4. Test your implementation

### Best Practices
1. Keep services focused and testable
2. Use type hints for clarity
3. Document complex logic
4. Test edge cases
5. Follow existing patterns

---

## 🎓 Educational Value

This MVP demonstrates:
- ✅ Modular Python architecture
- ✅ SQLAlchemy ORM patterns
- ✅ Vector database operations
- ✅ FastAPI best practices
- ✅ React/Next.js patterns
- ✅ Type-safe TypeScript
- ✅ Abstract provider patterns
- ✅ REST API design

Use this as a template for similar systems!

---

## 📝 Version Info

**Current Version**: 0.1.0 MVP  
**Python**: 3.10+  
**Node.js**: 18+  
**PostgreSQL**: 14+  

**Status**: ✅ **Stable and ready for development**

---

## 🗺️ Roadmap

### V0.1.0 (Current)
- [x] Core memory system
- [x] Semantic retrieval
- [x] LLM integration
- [x] Basic UI
- [x] Memory inspector

### V0.2.0 (Planned)
- [ ] File upload support
- [ ] Multi-LLM providers
- [ ] Advanced memory UI
- [ ] Memory compression

### V0.3.0 (Future)
- [ ] Multi-agent support
- [ ] Memory graphs
- [ ] Advanced analytics
- [ ] Production deployment guide

### V1.0.0 (Long-term)
- [ ] Enterprise features
- [ ] Distributed memory
- [ ] Advanced AI capabilities
- [ ] Commercial support

---

## 📖 Documentation Tips

- **New to MemLayer?** Start with QUICKSTART.md
- **Need a reference?** Check API.md
- **Want to extend?** Read DEVELOPMENT.md
- **Need details?** See README.md and ARCHITECTURE.md
- **Verifying progress?** Check CHECKLIST.md

---

**Happy building! 🚀**

For specific questions, refer to the relevant documentation file above.
