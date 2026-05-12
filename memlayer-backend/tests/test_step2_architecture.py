"""
Basic integration tests for Step 2 architecture.

These tests verify:
- Provider factory and registration
- Context layers structure
- Message processing pipeline
- Structured context compilation
"""

import pytest
from app.services.providers import (
    ProviderFactory,
    ProviderType,
    GenerationConfig,
    GenerationResult,
)
from app.schemas.context import (
    ContextLayers,
    CompilationStrategy,
    CompilationMetadata,
    ChatHistoryLayer,
    MemoryLayer,
    WorkspaceSummaryLayer,
)


class TestProviderFactory:
    """Test provider factory and registration."""

    def test_provider_registration(self):
        """Verify all providers are registered."""
        available = ProviderFactory.get_available_providers()
        assert "gemini" in available
        assert "openai" in available
        assert "claude" in available

    def test_generation_result_creation(self):
        """Test GenerationResult dataclass."""
        result = GenerationResult(
            text="Test response",
            provider="gemini",
            model="gemini-pro",
            tokens_used=100,
            tokens_estimated=150,
            latency_ms=1234.5,
            metadata={"finish_reason": "STOP"},
        )

        assert result.text == "Test response"
        assert result.provider == "gemini"
        assert result.tokens_used == 100
        assert result.latency_ms == 1234.5

    def test_generation_config_defaults(self):
        """Test GenerationConfig defaults."""
        config = GenerationConfig()
        assert config.temperature == 0.7
        assert config.top_p == 0.9
        assert config.max_tokens == 2048


class TestContextLayers:
    """Test context layer structure."""

    def test_context_layers_creation(self):
        """Test creating structured context layers."""
        chat_history = ChatHistoryLayer(
            messages=[
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T00:00:00",
                },
                {
                    "role": "assistant",
                    "content": "Hi there!",
                    "timestamp": "2024-01-01T00:00:01",
                },
            ],
            message_count=2,
        )

        metadata = CompilationMetadata(
            provider="gemini",
            model="gemini-pro",
            compilation_strategy=CompilationStrategy.FULL_CONTEXT,
            token_estimate=500,
            token_limit=2000,
            retrieved_memory_ids=["mem1", "mem2"],
            retrieved_scores=[0.9, 0.8],
        )

        context = ContextLayers(
            chat_history=chat_history,
            semantic_memories=[],
            workspace_summary=WorkspaceSummaryLayer(),
            metadata=metadata,
            compiled_prompt="Test prompt",
        )

        assert context.metadata.provider == "gemini"
        assert len(context.chat_history.messages) == 2
        assert context.metadata.token_estimate == 500

    def test_memory_layer_creation(self):
        """Test creating memory layers."""
        from datetime import datetime, timezone

        memory = MemoryLayer(
            id="test-id",
            content="Test memory content",
            source_type="user_message",
            importance_score=0.8,
            similarity_score=0.9,
            timestamp=datetime.now(timezone.utc),
            metadata={"key": "value"},
        )

        assert memory.id == "test-id"
        assert memory.similarity_score == 0.9
        assert memory.importance_score == 0.8


class TestCompilationStrategy:
    """Test compilation strategies."""

    def test_compilation_strategies_enum(self):
        """Verify compilation strategies."""
        assert CompilationStrategy.FULL_CONTEXT.value == "full_context"
        assert CompilationStrategy.COMPRESSED.value == "compressed"
        assert CompilationStrategy.MINIMAL.value == "minimal"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
