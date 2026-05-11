# Development Guide

How to extend and customize MemLayer for your needs.

## Adding a New LLM Provider

The system uses an abstract `LLMProvider` interface, making it easy to add new models.

### 1. Create Provider Class

**File:** `memlayer-backend/app/services/llm.py`

```python
class OpenAIProvider(LLMProvider):
    """OpenAI API integration."""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        # Initialize OpenAI client
        import openai
        openai.api_key = self.api_key
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from OpenAI."""
        import openai
        
        response = openai.ChatCompletion.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
        )
        return response.choices[0].message.content
    
    def generate_with_context(
        self,
        context: str,
        query: str,
        **kwargs
    ) -> str:
        """Generate response with context."""
        prompt = f"""{context}

Query: {query}

Response:"""
        return self.generate(prompt, **kwargs)
```

### 2. Register Provider

```python
from app.services.llm import LLMService, OpenAIProvider

# In your initialization
provider = OpenAIProvider()
llm_service = LLMService(provider)
```

---

## Adding a New Embedding Provider

Memory embeddings can come from different sources.

### 1. Create Provider Class

**File:** `memlayer-backend/app/services/embedding.py`

```python
class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embeddings API."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-3-small"):
        import openai
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        openai.api_key = self.api_key
    
    def embed(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings using OpenAI."""
        import openai
        
        if isinstance(text, str):
            text = [text]
        
        response = openai.Embedding.create(
            input=text,
            model=self.model
        )
        
        embeddings = [item["embedding"] for item in response["data"]]
        return embeddings[0] if len(embeddings) == 1 else embeddings
    
    def get_dimension(self) -> int:
        """Get embedding dimension."""
        # OpenAI small: 512, large: 1536
        return 1536
```

### 2. Update Configuration

**File:** `.env`

```
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## Adding File Upload Support

Extend memory storage to handle files.

### 1. Create Upload Handler

**File:** `memlayer-backend/app/services/file_handler.py`

```python
import fitz  # PyMuPDF for PDFs
from typing import List

class FileHandler:
    """Handles file uploads and text extraction."""
    
    @staticmethod
    def extract_pdf_text(file_path: str) -> List[str]:
        """Extract text from PDF file."""
        doc = fitz.open(file_path)
        texts = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            texts.append({
                "content": text,
                "page": page_num + 1,
            })
        
        return texts
    
    @staticmethod
    def extract_text_file(file_path: str) -> str:
        """Extract text from plain text file."""
        with open(file_path, 'r') as f:
            return f.read()
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        for i in range(0, len(text), chunk_size - overlap):
            chunks.append(text[i:i + chunk_size])
        return chunks
```

### 2. Add Upload Endpoint

**File:** `memlayer-backend/app/api/files.py`

```python
from fastapi import APIRouter, UploadFile, File, Depends
from app.services.file_handler import FileHandler
from app.services.memory_storage import MemoryStorageService

router = APIRouter(prefix="/api/workspaces/{workspace_id}/upload", tags=["files"])

@router.post("/pdf")
async def upload_pdf(
    workspace_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload and process PDF file."""
    # Save file
    file_path = f"/tmp/{file.filename}"
    with open(file_path, 'wb') as f:
        f.write(await file.read())
    
    # Extract text
    texts = FileHandler.extract_pdf_text(file_path)
    
    # Create memories
    service = MemoryStorageService(db)
    memories = []
    
    for item in texts:
        chunks = FileHandler.chunk_text(item["content"])
        for chunk in chunks:
            memory = service.create_memory(
                workspace_id=workspace_id,
                raw_content=chunk,
                source_type="file_upload",
                metadata={
                    "file_name": file.filename,
                    "page": item["page"],
                }
            )
            memories.append(memory)
    
    return {"created_memories": len(memories), "file": file.filename}
```

---

## Customizing Memory Importance

Make importance scores dynamic based on usage patterns.

### 1. Update Memory Model

**File:** `memlayer-backend/app/db/models.py`

```python
class Memory(Base):
    # ... existing fields ...
    
    # Add tracking fields
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    def compute_dynamic_importance(self) -> float:
        """Compute importance based on usage and recency."""
        from datetime import datetime, timedelta
        
        # Base importance
        importance = self.importance_score
        
        # Boost based on recent access
        if self.last_accessed:
            days_since = (datetime.utcnow() - self.last_accessed).days
            recency_boost = 0.1 * max(0, 1 - days_since / 30)
            importance += recency_boost
        
        # Boost based on frequency
        access_boost = 0.1 * min(1.0, self.access_count / 10)
        importance += access_boost
        
        # Boost based on relevance
        if self.relevance_score:
            importance += self.relevance_score * 0.2
        
        return min(1.0, importance)
```

### 2. Update Retrieval Service

```python
def retrieve(self, workspace_id: str, query: str, **kwargs) -> Tuple[List[Memory], List[float]]:
    # ... existing retrieval code ...
    
    # Apply dynamic importance
    memories_with_scores = []
    for memory, similarity in zip(memories, similarities):
        dynamic_importance = memory.compute_dynamic_importance()
        weighted_score = (similarity * 0.6) + (dynamic_importance * 0.4)
        memories_with_scores.append((memory, weighted_score))
        
        # Update access tracking
        memory.access_count += 1
        memory.last_accessed = datetime.utcnow()
    
    self.db.commit()
    return memories_with_scores
```

---

## Adding Memory Compression

Reduce storage for old memories while preserving information.

### 1. Create Compression Service

**File:** `memlayer-backend/app/services/memory_compression.py`

```python
class MemoryCompressionService:
    """Compresses memories to reduce storage."""
    
    def __init__(self, db: Session, llm_service):
        self.db = db
        self.llm_service = llm_service
    
    def compress_memory(self, memory: Memory) -> str:
        """Summarize memory into key facts."""
        prompt = f"""Summarize the following text into 1-2 sentences, keeping only essential facts:

{memory.raw_content}

Summary:"""
        
        compressed = self.llm_service.generate(prompt, max_tokens=100)
        return compressed
    
    def compress_old_memories(self, workspace_id: str, days_old: int = 30):
        """Compress memories older than specified days."""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_memories = self.db.query(Memory).filter(
            Memory.workspace_id == workspace_id,
            Memory.timestamp < cutoff_date,
        ).all()
        
        for memory in old_memories:
            compressed = self.compress_memory(memory)
            memory.raw_content = compressed
            memory.metadata['compressed'] = True
        
        self.db.commit()
        return len(old_memories)
```

---

## Adding Memory Categories

Organize memories by topic/category.

### 1. Update Model

```python
class Memory(Base):
    # ... existing fields ...
    
    category = Column(String, nullable=True)
    tags = Column(JSON, default=[], nullable=True)
```

### 2. Update Retrieval

```python
def retrieve_by_category(
    self,
    workspace_id: str,
    category: str,
    query: str,
    top_k: int = 5,
):
    """Retrieve memories filtered by category."""
    results = self.db.query(
        Memory,
        func.similarity(Memory.embedding, query_embedding)
    ).filter(
        Memory.workspace_id == workspace_id,
        Memory.category == category,
    ).order_by('similarity').limit(top_k).all()
    
    return results
```

---

## Testing Your Extensions

### 1. Unit Tests

**File:** `memlayer-backend/tests/test_custom_provider.py`

```python
import pytest
from app.services.llm import OpenAIProvider

@pytest.fixture
def openai_provider():
    return OpenAIProvider(api_key="test-key")

def test_generate(openai_provider):
    # Mock the API call
    result = openai_provider.generate("Hello")
    assert isinstance(result, str)
```

### 2. Integration Tests

```python
def test_full_pipeline_with_custom_llm(db, workspace_id):
    from app.services.chat_orchestration import ChatOrchestrationService
    from app.services.llm import OpenAIProvider, LLMService
    
    # Replace default provider
    provider = OpenAIProvider()
    service = ChatOrchestrationService(db)
    service.llm_service = LLMService(provider)
    
    result = service.process_message(workspace_id, chat_id, "Test query")
    assert "response" in result
```

---

## Performance Tuning

### 1. Optimize Embeddings

```python
# Use batch processing
embeddings = embedding_service.embed_batch(texts, batch_size=64)

# Enable GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
```

### 2. Database Optimization

```python
# Create indices on frequently queried fields
from sqlalchemy import Index

# In models.py
Index('idx_memory_timestamp', Memory.timestamp)
Index('idx_memory_workspace', Memory.workspace_id)

# Create vector index
CREATE INDEX ON memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> List[float]:
    """Cache embeddings to avoid recomputation."""
    return embedding_service.embed(text)
```

---

## Monitoring and Logging

### 1. Add Logging

```python
import logging

logger = logging.getLogger(__name__)

def retrieve(self, workspace_id: str, query: str):
    logger.info(f"Retrieving memories for workspace: {workspace_id}")
    
    try:
        memories, scores = self._semantic_search(query)
        logger.info(f"Retrieved {len(memories)} memories")
        return memories, scores
    except Exception as e:
        logger.error(f"Retrieval failed: {str(e)}")
        raise
```

### 2. Add Metrics

```python
from prometheus_client import Counter, Histogram

query_count = Counter('queries_total', 'Total queries processed')
query_duration = Histogram('query_duration_seconds', 'Query processing time')

@query_duration.time()
def process_message(self, ...):
    query_count.inc()
    # ... existing code ...
```

---

## Deployment Checklist

Before production:

- [ ] Set `DEBUG=false` in config
- [ ] Use strong database passwords
- [ ] Enable CORS properly
- [ ] Set rate limiting
- [ ] Add authentication layer
- [ ] Configure logging to files
- [ ] Set up monitoring
- [ ] Test error handling
- [ ] Document custom extensions
- [ ] Create backup strategy

---

## Contributing

To contribute improvements:

1. Create feature branch
2. Add tests
3. Update documentation
4. Create PR with clear description
5. Follow existing code style

## Resources

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [pgvector](https://github.com/pgvector/pgvector)
- [Sentence Transformers](https://www.sbert.net/)
