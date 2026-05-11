"""
Tests for Context Compression Engine (Phase 3).

Tests verify:
1. Compression across all 5 modes
2. Semantic retention evaluation
3. Provider-aware optimization
4. Token budget simulation
5. Compression stability and reproducibility
6. Entity/topic/reasoning preservation
7. Edge cases and robustness
"""

import pytest
import re
from unittest.mock import Mock
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Mock embedding service
sys.modules["app.services.embedding"] = Mock()

from app.compiler.context_compression import (
    ContextCompressionService,
    CompressionMode,
    ProviderType,
    CompressedContext,
    CompressionMetrics,
    TokenBudgetSimulator,
)


class TestContextCompressionService:
    """Test compression service functionality."""

    @pytest.fixture
    def compression_service(self):
        """Create compression service."""
        mock_embedding_service = Mock()
        return ContextCompressionService(embedding_service=mock_embedding_service)

    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """
        The artificial intelligence system has been trained on extensive datasets 
        including books, articles, and academic papers. The model uses transformer 
        architecture with attention mechanisms to process information. Key capabilities 
        include natural language understanding, text generation, and reasoning tasks. 
        Performance on benchmark tests shows strong results across multiple domains.
        Recent improvements have focused on reducing hallucinations and improving 
        factual accuracy. The system now supports context lengths up to 32k tokens, 
        allowing for more comprehensive analysis and longer conversations.
        """

    def test_full_context_compression(self, compression_service, sample_content):
        """Test FULL_CONTEXT mode preserves maximum fidelity."""
        result = compression_service.compress_context(
            sample_content, mode=CompressionMode.FULL_CONTEXT
        )

        # Full context should have minimal compression
        assert result.compression_ratio < 0.1
        assert result.semantic_retention > 0.9
        assert result.compression_mode == CompressionMode.FULL_CONTEXT

    def test_compressed_mode(self, compression_service, sample_content):
        """Test COMPRESSED mode balances efficiency and fidelity."""
        result = compression_service.compress_context(
            sample_content, mode=CompressionMode.COMPRESSED
        )

        # Balanced mode should achieve reasonable compression
        assert 0.2 < result.compression_ratio < 0.6
        assert result.semantic_retention > 0.6
        assert len(result.summary) > 0

    def test_minimal_compression(self, compression_service, sample_content):
        """Test MINIMAL mode aggressively compresses."""
        result = compression_service.compress_context(
            sample_content, mode=CompressionMode.MINIMAL
        )

        # Minimal should achieve high compression
        assert result.compression_ratio > 0.5
        assert result.compressed_tokens < result.original_tokens

    def test_research_mode_preservation(self, compression_service):
        """Test RESEARCH_MODE preserves citations and facts."""
        research_content = """
        According to Smith et al. [2023], the model achieved 95.2% accuracy on GLUE.
        Related work by Jones (2022) demonstrates similar results. The methodology 
        involves training on 2.8 trillion tokens with a batch size of 4096. As shown 
        in Table 1, performance improves with scale. "This represents significant 
        progress" as noted in the original paper.
        """

        result = compression_service.compress_context(
            research_content, mode=CompressionMode.RESEARCH_MODE
        )

        # Research mode should preserve citations and numbers
        assert "[" in result.summary or "%" in result.summary or "2" in result.summary
        # Retention should be reasonable
        assert result.semantic_retention > 0.3

    def test_coding_mode_preservation(self, compression_service):
        """Test CODING_MODE preserves technical precision."""
        code_content = """
        The main function is defined as def process_data(input_tensor). 
        It uses model.forward(x) to compute predictions. The loss is calculated 
        using torch.nn.CrossEntropyLoss(). Configuration includes learning_rate=0.001 
        and batch_size=32. The architecture uses self.linear1 = nn.Linear(128, 64).
        """

        result = compression_service.compress_context(
            code_content, mode=CompressionMode.CODING_MODE
        )

        # Coding mode should preserve technical elements
        assert "(" in result.summary or "=" in result.summary or "." in result.summary
        assert result.compression_mode == CompressionMode.CODING_MODE

    def test_claude_optimization(self, compression_service, sample_content):
        """Test Claude-optimized compression."""
        result = compression_service.compress_context(
            sample_content,
            mode=CompressionMode.COMPRESSED,
            provider=ProviderType.CLAUDE,
        )

        assert result.provider_type == ProviderType.CLAUDE
        assert result.compressed_tokens > 0
        # Claude optimization should preserve reasoning structure
        assert result.reasoning_continuity > 0.3

    def test_openai_optimization(self, compression_service, sample_content):
        """Test OpenAI-optimized compression."""
        result = compression_service.compress_context(
            sample_content,
            mode=CompressionMode.COMPRESSED,
            provider=ProviderType.OPENAI,
        )

        assert result.provider_type == ProviderType.OPENAI
        # OpenAI prefers concise context
        assert len(result.summary) < len(sample_content)

    def test_gemini_optimization(self, compression_service, sample_content):
        """Test Gemini-optimized compression."""
        result = compression_service.compress_context(
            sample_content,
            mode=CompressionMode.COMPRESSED,
            provider=ProviderType.GEMINI,
        )

        assert result.provider_type == ProviderType.GEMINI
        assert result.semantic_retention > 0.5

    def test_token_budget_constraint(self, compression_service, sample_content):
        """Test compression respects token budget."""
        token_budget = 50  # Very tight budget

        result = compression_service.compress_context(
            sample_content,
            mode=CompressionMode.MINIMAL,
            provider=ProviderType.CLAUDE,
            token_budget=token_budget,
        )

        # Should respect budget approximately
        assert result.compressed_tokens <= token_budget * 1.2  # Allow 20% overage

    def test_empty_content(self, compression_service):
        """Test handling of empty content."""
        result = compression_service.compress_context("")

        assert result.original_tokens == 0
        assert result.compressed_tokens == 0
        assert result.semantic_retention == 0.0

    def test_entity_retention(self, compression_service):
        """Test entity retention in compression."""
        content = "Alice and Bob discussed the latest AI breakthrough by OpenAI."

        result = compression_service.compress_context(
            content, mode=CompressionMode.COMPRESSED
        )

        # Should retain some semantic information
        assert result.semantic_retention > 0.0
        # Compression time should be measurable
        assert result.compression_time_ms > 0

    def test_topic_retention(self, compression_service):
        """Test topic retention."""
        content = """
        Neural networks learn through backpropagation. The learning process involves 
        computing gradients and updating weights. Different neural architectures 
        including CNNs, RNNs, and Transformers have different properties.
        """

        result = compression_service.compress_context(
            content, mode=CompressionMode.COMPRESSED
        )

        # Should preserve semantic meaning
        assert result.semantic_retention > 0.3

    def test_reasoning_continuity(self, compression_service):
        """Test reasoning continuity preservation."""
        logical_content = """
        Because the model has strong performance, therefore it can be deployed. 
        If the budget allows, then we should implement it. Thus the implementation 
        can proceed. This means users will benefit from improved accuracy.
        """

        result = compression_service.compress_context(
            logical_content, mode=CompressionMode.COMPRESSED
        )

        # Logical connectors should be preserved
        assert result.reasoning_continuity > 0.0

    def test_compression_reproducibility(self, compression_service, sample_content):
        """Test compression produces reproducible results."""
        result1 = compression_service.compress_context(
            sample_content, mode=CompressionMode.COMPRESSED
        )
        result2 = compression_service.compress_context(
            sample_content, mode=CompressionMode.COMPRESSED
        )

        # Same mode, same content should produce same compression ratio
        assert result1.compression_ratio == result2.compression_ratio

    def test_semantic_retention_metrics(self, compression_service, sample_content):
        """Test semantic retention metrics are calculated."""
        result = compression_service.compress_context(sample_content)

        assert hasattr(result, "semantic_retention")
        assert hasattr(result, "entity_retention")
        assert hasattr(result, "topic_retention")
        assert hasattr(result, "reasoning_continuity")
        assert 0.0 <= result.semantic_retention <= 1.0


class TestTokenBudgetSimulator:
    """Test token budget simulation."""

    def test_claude_budgets(self):
        """Test Claude provider budgets."""
        budgets = TokenBudgetSimulator.get_available_budgets(ProviderType.CLAUDE)

        assert "4k" in budgets
        assert "8k" in budgets
        assert "16k" in budgets
        assert "32k" in budgets
        assert budgets["4k"] == 4000

    def test_openai_budgets(self):
        """Test OpenAI provider budgets."""
        budgets = TokenBudgetSimulator.get_available_budgets(ProviderType.OPENAI)

        assert "4k" in budgets
        assert "128k" in budgets

    def test_compression_required_calculation(self):
        """Test compression ratio calculation."""
        # No compression needed when context fits
        ratio = TokenBudgetSimulator.calculate_compression_required(
            context_tokens=1000, budget=4000
        )
        assert ratio == 0.0

        # Compression needed when context exceeds budget
        ratio = TokenBudgetSimulator.calculate_compression_required(
            context_tokens=5000, budget=4000
        )
        assert ratio > 0.0
        assert ratio < 1.0

        # Extreme compression needed for very small budget
        ratio = TokenBudgetSimulator.calculate_compression_required(
            context_tokens=10000, budget=1000
        )
        assert 0.5 < ratio <= 1.0

    def test_compression_with_reserve(self):
        """Test compression calculation with response reserve."""
        # With 20% reserve for response
        ratio = TokenBudgetSimulator.calculate_compression_required(
            context_tokens=5000, budget=4000, reserve=0.2
        )

        # Should require compression to fit in 80% of budget (3200 tokens)
        assert ratio > 0.0


class TestCompressionMetrics:
    """Test compression metrics."""

    def test_metrics_creation(self):
        """Test metrics initialization."""
        metrics = CompressionMetrics(
            total_input_tokens=10000,
            total_output_tokens=5000,
            num_contexts_compressed=5,
        )

        assert metrics.total_input_tokens == 10000
        assert metrics.total_output_tokens == 5000
        assert metrics.num_contexts_compressed == 5
        # overall_compression_ratio is calculated, verify it's initialized
        assert metrics.overall_compression_ratio >= 0.0


class TestCompressedContext:
    """Test compressed context structure."""

    def test_context_creation(self):
        """Test creating compressed context."""
        ctx = CompressedContext(
            original_tokens=1000,
            compressed_tokens=500,
            compression_ratio=0.5,
            semantic_retention=0.85,
            entity_retention=0.9,
        )

        assert ctx.original_tokens == 1000
        assert ctx.compressed_tokens == 500
        assert ctx.semantic_retention == 0.85

    def test_context_default_values(self):
        """Test default values in compressed context."""
        ctx = CompressedContext()

        assert ctx.original_tokens == 0
        assert ctx.compression_mode == CompressionMode.COMPRESSED
        assert ctx.provider_type == ProviderType.GENERIC
        assert isinstance(ctx.entities, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
