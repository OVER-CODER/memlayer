# MemLayer Step 2 - Developer Quick Reference

## Quick Start

### Using the LLM Service (Provider-Agnostic)

```python
from app.services.llm import get_llm_service
from app.services.providers import GenerationConfig

# Get default LLM service
llm = get_llm_service()

# Generate response
config = GenerationConfig(temperature=0.7, max_tokens=1024)
result = llm.generate("What is AI?", config)

print(f"Provider: {result.provider}")
print(f"Tokens: {result.tokens_used}")
print(f"Latency: {result.latency_ms}ms")
print(f"Response: {result.text}")
```

### Switching Providers at Runtime

```python
from app.services.llm import get_llm_service

llm = get_llm_service()

# Switch to OpenAI
llm.switch_provider("openai", model="gpt-4")

# Generate with new provider
result = llm.generate("What is AI?")

# Switch to Claude
llm.switch_provider("claude", model="claude-3-opus")
result = llm.generate("What is AI?")
```

### Processing Messages with Provider Selection

```python
from app.services.chat_orchestration import ChatOrchestrationService

service = ChatOrchestrationService(db)

# Process with specific provider
result = service.process_message(
    workspace_id="ws-123",
    chat_id="chat-456",
    query="Hello!",
    provider="openai",      # Optional: override default
    model="gpt-4"           # Optional: override default
)

print(f"Used: {result['provider_used']}")
print(f"Tokens: {result['tokens_used']}")
print(f"Response: {result['response']}")
```

### Working with Context Layers

```python
from app.services.context_compilation import ContextCompilationService
from app.schemas.context import CompilationStrategy

service = ContextCompilationService(db)

# Compile structured context
context = service.compile_context(
    workspace_id="ws-123",
    chat_id="chat-456",
    query="What did we discuss?",
    retrieved_memories=memories,
    retrieved_scores=scores,
    provider="gemini",
    model="gemini-pro",
    compilation_strategy=CompilationStrategy.FULL_CONTEXT
)

# Access layers
print(f"Chat history: {len(context.chat_history.messages)} messages")
print(f"Memories: {len(context.semantic_memories)}")
print(f"Tokens: {context.metadata.token_estimate}")
```

### Inspecting Context

```python
from app.services.context_inspector import ContextInspector

# Get debug report
report = ContextInspector.format_context_report(context)
print(report)

# Check token distribution
distribution = ContextInspector.inspect_token_distribution(context)
for layer, tokens in distribution.items():
    print(f"{layer}: {tokens}")

# Export debug info
debug_json = ContextInspector.export_debug_json(context, compiled_prompt)
```

### Managing Workspace Summaries

```python
from app.services.workspace_summary import WorkspaceSummaryService

service = WorkspaceSummaryService(db)

# Conditionally update summary
updated = service.maybe_update_summary(workspace_id="ws-123")

# Or force update
updated = service.maybe_update_summary(workspace_id="ws-123", force=True)

# Get current summary
summary = service.get_summary(workspace_id="ws-123")
print(f"Summary: {summary.summary_text}")
print(f"Topics: {summary.key_topics}")
```

## API Usage

### Send Message with Provider Selection

```bash
curl -X POST http://localhost:8000/api/chats/chat-456/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k_memories": 5,
    "similarity_threshold": 0.3,
    "provider": "openai",
    "model": "gpt-4"
  }'
```

### Response Example

```json
{
  "message_id": "msg-123",
  "response": "Machine learning is...",
  "provider_used": "openai",
  "model_used": "gpt-4",
  "tokens_used": 145,
  "latency_ms": 1234.5,
  "retrieved_memories": [
    {
      "id": "mem-1",
      "content": "ML is a subset of AI...",
      "similarity_score": 0.92,
      "importance_score": 0.8
    }
  ],
  "context_metadata": {
    "provider": "openai",
    "model": "gpt-4",
    "compilation_strategy": "full_context",
    "token_estimate": 250,
    "token_limit": 2000
  }
}
```

## Configuration

### Environment Variables

```bash
# Required for Gemini
GEMINI_API_KEY=...

# Optional for OpenAI
OPENAI_API_KEY=sk-...

# Optional for Claude
ANTHROPIC_API_KEY=sk-ant-...

# Default settings
DEFAULT_PROVIDER=gemini          # gemini, openai, or claude
DEFAULT_MODEL=gemini-pro         # Model name for provider

# Database
DATABASE_URL=postgresql://...

# Memory settings
MEMORY_RETRIEVAL_THRESHOLD=0.3
TOP_K_MEMORIES=5
```

## Common Patterns

### Pattern 1: Simple Query with Default Provider

```python
service = ChatOrchestrationService(db)
result = service.process_message(
    workspace_id=ws_id,
    chat_id=chat_id,
    query="Hello!"
)
```

### Pattern 2: Compare Providers

```python
for provider in ["gemini", "openai", "claude"]:
    llm = LLMService(provider_type=provider)
    result = llm.generate(prompt)
    print(f"{provider}: {result.latency_ms}ms, {result.tokens_used} tokens")
```

### Pattern 3: Analyze Context Quality

```python
context = service.compile_context(...)
report = ContextInspector.format_context_report(context)
distribution = ContextInspector.inspect_token_distribution(context)

# Ensure enough memories are included
if len(context.semantic_memories) < 3:
    print("Warning: Few relevant memories found")

# Check if context fits in token limit
if context.metadata.token_estimate > context.metadata.token_limit * 0.9:
    print("Warning: Context near token limit")
```

### Pattern 4: Track Memory Lineage

```python
# Create memory from user message
user_memory = memory_storage.create_memory(
    workspace_id=ws_id,
    raw_content=query,
    source_type="user_message",
    generated_from_message_id=message.id,
    generated_by_provider="user"
)

# Create memory from LLM response
response_memory = memory_storage.create_memory(
    workspace_id=ws_id,
    raw_content=response,
    source_type="assistant_response",
    generated_from_message_id=message.id,
    generated_by_provider=result.provider,
    source_memory_ids=[m.id for m in retrieved_memories]
)
```

## File Locations

### Services
- `app/services/llm.py` - LLM service with provider switching
- `app/services/chat_orchestration.py` - Message processing pipeline
- `app/services/context_compilation.py` - Context layer assembly
- `app/services/memory_storage.py` - Memory management
- `app/services/workspace_summary.py` - Workspace summarization
- `app/services/context_inspector.py` - Debugging tools
- `app/services/providers/` - Provider implementations

### Schemas
- `app/schemas/context.py` - Context layer schemas
- `app/schemas/memory.py` - Memory and API schemas

### API
- `app/api/chats.py` - Chat endpoints

### Models
- `app/db/models.py` - Database models

### Config
- `app/core/config.py` - Configuration

## Testing

### Run Basic Integration Tests
```bash
pytest tests/test_step2_architecture.py -v
```

### Test Provider Factory
```bash
python -c "from app.services.providers import ProviderFactory; print(ProviderFactory.get_available_providers())"
```

## Troubleshooting

### Provider Not Found
**Error:** `ValueError: Unknown provider type: xyz`  
**Fix:** Check that provider name is `gemini`, `openai`, or `claude`

### Missing API Key
**Error:** `ValueError: No API key configured for provider: openai`  
**Fix:** Set `OPENAI_API_KEY` environment variable

### Token Limit Exceeded
**Solution:** Use `CompilationStrategy.COMPRESSED` to reduce context size

### Low Memory Retrieval
**Check:** `len(context.semantic_memories) < 3`  
**Solution:** Lower `similarity_threshold` or increase `top_k_memories`

## Performance Tips

1. **Use COMPRESSED strategy** for large workspaces
2. **Monitor latency** via `result.latency_ms`
3. **Track tokens** to optimize costs
4. **Cache workspace summaries** to reduce LLM calls
5. **Batch memory retrievals** when possible

## Future Enhancements

- [ ] Streaming response support
- [ ] Hybrid memory retrieval (BM25 + semantic)
- [ ] Adaptive context compression
- [ ] Provider-specific token counting
- [ ] Multi-turn conversation optimization
- [ ] Memory consolidation strategies

---

**Last Updated:** May 11, 2026  
**Version:** Step 2 Beta  
**Status:** 🟢 Production Ready
