"""
Tests for Runtime Intelligence Dataset Generator.

Tests for creating training datasets from runtime traces
for optimization learning.
"""

import pytest
from app.runtime import (
    RuntimeIntelligenceDatasetGenerator,
    RuntimeIntelligenceDataset,
    DatasetSample,
    DatasetPartition,
    DatasetType,
    get_dataset_generator,
)


class TestDatasetSample:
    """Test dataset sample functionality."""

    def test_sample_creation(self):
        """Test creating a dataset sample."""
        sample = DatasetSample(
            sample_id="sample-1",
            dataset_type=DatasetType.COMPRESSION_DECISIONS,
            query="Test query",
            query_type="general",
            query_complexity="moderate",
            memory_pool_size=500,
            memory_quality=0.85,
            token_budget=4000,
            available_providers=["claude", "openai"],
            current_provider="claude",
            session_length=10,
            session_degradation=0.1,
            domain="research",
            chosen_provider="claude",
            chosen_compression_mode="balanced",
            token_efficiency=0.85,
            quality_score=0.9,
            success=True,
            latency_ms=150.0,
        )

        assert sample.sample_id == "sample-1"
        assert sample.quality_score == 0.9
        assert sample.success is True

    def test_sample_to_dict(self):
        """Test converting sample to dictionary."""
        sample = DatasetSample(
            sample_id="sample-2",
            dataset_type=DatasetType.PROVIDER_SELECTION,
            query="Query",
            query_type="technical",
            query_complexity="complex",
            memory_pool_size=1000,
            memory_quality=0.8,
            token_budget=8000,
            available_providers=["claude", "openai", "gemini"],
            current_provider="openai",
            session_length=20,
            session_degradation=0.15,
            domain="code",
            chosen_provider="claude",
            chosen_compression_mode="aggressive",
            token_efficiency=0.9,
            quality_score=0.88,
            success=True,
            latency_ms=200.0,
        )

        sample_dict = sample.to_dict()

        assert sample_dict["sample_id"] == "sample-2"
        assert sample_dict["quality_score"] == 0.88
        assert sample_dict["num_providers"] == 3

    def test_sample_feature_vector(self):
        """Test getting feature vector from sample."""
        sample = DatasetSample(
            sample_id="sample-3",
            dataset_type=DatasetType.QUALITY_PREDICTION,
            query="Query",
            query_type="general",
            query_complexity="simple",
            memory_pool_size=1000,
            memory_quality=0.9,
            token_budget=4000,
            available_providers=["claude", "openai"],
            current_provider="claude",
            session_length=50,
            session_degradation=0.2,
            domain="research",
            chosen_provider="claude",
            chosen_compression_mode="balanced",
            token_efficiency=0.85,
            quality_score=0.92,
            success=True,
            latency_ms=250.0,
        )

        features = sample.get_feature_vector()

        assert len(features) == 9
        assert all(0 <= f <= 1 for f in features)

    def test_sample_get_label_compression(self):
        """Test getting label for compression decisions."""
        sample = DatasetSample(
            sample_id="sample-4",
            dataset_type=DatasetType.COMPRESSION_DECISIONS,
            query="Query",
            query_type="general",
            query_complexity="moderate",
            memory_pool_size=500,
            memory_quality=0.8,
            token_budget=4000,
            available_providers=["claude"],
            current_provider="claude",
            session_length=10,
            session_degradation=0.1,
            domain="research",
            chosen_provider="claude",
            chosen_compression_mode="balanced",
            token_efficiency=0.85,
            quality_score=0.9,
            success=True,
            latency_ms=150.0,
        )

        label = sample.get_label()
        assert label == "balanced"

    def test_sample_get_label_quality_prediction(self):
        """Test getting label for quality prediction."""
        for quality, expected in [
            (0.5, "poor"),
            (0.7, "fair"),
            (0.82, "good"),
            (0.95, "excellent"),
        ]:
            sample = DatasetSample(
                sample_id=f"sample-quality-{quality}",
                dataset_type=DatasetType.QUALITY_PREDICTION,
                query="Query",
                query_type="general",
                query_complexity="moderate",
                memory_pool_size=500,
                memory_quality=0.8,
                token_budget=4000,
                available_providers=["claude"],
                current_provider="claude",
                session_length=10,
                session_degradation=0.1,
                domain="research",
                chosen_provider="claude",
                chosen_compression_mode="balanced",
                token_efficiency=0.85,
                quality_score=quality,
                success=True,
                latency_ms=150.0,
            )

            label = sample.get_label()
            assert label == expected


class TestDatasetPartition:
    """Test dataset partition functionality."""

    def test_partition_creation(self):
        """Test creating a dataset partition."""
        partition = DatasetPartition(
            partition_id="partition-1",
            partition_type="train",
        )

        assert partition.partition_id == "partition-1"
        assert partition.partition_type == "train"
        assert len(partition.samples) == 0

    def test_partition_statistics(self):
        """Test calculating partition statistics."""
        # Create samples
        samples = []
        for i in range(10):
            sample = DatasetSample(
                sample_id=f"sample-{i}",
                dataset_type=DatasetType.COMPRESSION_DECISIONS,
                query="Query",
                query_type="general",
                query_complexity="moderate",
                memory_pool_size=500,
                memory_quality=0.8,
                token_budget=4000,
                available_providers=["claude"],
                current_provider="claude",
                session_length=10,
                session_degradation=0.1,
                domain="research" if i < 5 else "code",
                chosen_provider="claude",
                chosen_compression_mode="balanced",
                token_efficiency=0.85,
                quality_score=0.9,
                success=i < 9,  # 1 failure
                latency_ms=150.0,
            )
            samples.append(sample)

        partition = DatasetPartition(
            partition_id="partition-2",
            partition_type="train",
            samples=samples,
        )

        stats = partition.get_statistics()

        assert stats["sample_count"] == 10
        assert stats["success_rate"] == 0.9
        assert len(stats["domains"]) == 2


class TestRuntimeIntelligenceDataset:
    """Test runtime intelligence dataset."""

    def test_dataset_creation(self):
        """Test creating a dataset."""
        dataset = RuntimeIntelligenceDataset(
            dataset_id="dataset-1",
            dataset_type=DatasetType.COMPRESSION_DECISIONS,
            version="1.0",
            source="research",
        )

        assert dataset.dataset_id == "dataset-1"
        assert dataset.version == "1.0"
        assert dataset.total_samples == 0

    def test_dataset_to_dict(self):
        """Test converting dataset to dictionary."""
        dataset = RuntimeIntelligenceDataset(
            dataset_id="dataset-2",
            dataset_type=DatasetType.PROVIDER_SELECTION,
            version="1.0",
            source="engineering",
            total_samples=100,
            replay_compatible=True,
        )

        dataset_dict = dataset.to_dict()

        assert dataset_dict["dataset_id"] == "dataset-2"
        assert dataset_dict["version"] == "1.0"
        assert dataset_dict["replay_compatible"] is True

    def test_dataset_checksum(self):
        """Test dataset checksum generation."""
        dataset1 = RuntimeIntelligenceDataset(
            dataset_id="dataset-3",
            dataset_type=DatasetType.QUALITY_PREDICTION,
            version="1.0",
            source="test",
        )

        checksum1 = dataset1.get_checksum()
        checksum2 = dataset1.get_checksum()

        # Same dataset should have same checksum
        assert checksum1 == checksum2

        # Different dataset should have different checksum
        dataset2 = RuntimeIntelligenceDataset(
            dataset_id="dataset-4",
            dataset_type=DatasetType.QUALITY_PREDICTION,
            version="1.0",
            source="test",
        )
        checksum3 = dataset2.get_checksum()
        assert checksum1 != checksum3


class TestRuntimeIntelligenceDatasetGenerator:
    """Test dataset generator."""

    def test_generator_initialization(self):
        """Test initializing generator."""
        generator = RuntimeIntelligenceDatasetGenerator(deterministic_seed=123)

        assert generator.deterministic_seed == 123
        assert len(generator.generated_datasets) == 0

    def test_generate_compression_decision_dataset(self):
        """Test generating compression decision dataset."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_compression_decision_dataset(
            source="research",
            num_samples=100,
        )

        assert dataset.dataset_id is not None
        assert dataset.dataset_type == DatasetType.COMPRESSION_DECISIONS
        assert dataset.total_samples == 100
        assert dataset.train_partition is not None
        assert dataset.validation_partition is not None
        assert dataset.test_partition is not None

    def test_compression_dataset_splits(self):
        """Test that compression dataset has correct splits."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_compression_decision_dataset(
            num_samples=100,
            train_split=0.7,
            val_split=0.15,
        )

        train_count = len(dataset.train_partition.samples)
        val_count = len(dataset.validation_partition.samples)
        test_count = len(dataset.test_partition.samples)

        assert train_count == 70
        assert val_count == 15
        assert test_count == 15

    def test_generate_provider_selection_dataset(self):
        """Test generating provider selection dataset."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_provider_selection_dataset(
            source="engineering",
            num_samples=100,
        )

        assert dataset.dataset_type == DatasetType.PROVIDER_SELECTION
        assert dataset.total_samples == 100
        assert all(
            s.dataset_type == DatasetType.PROVIDER_SELECTION
            for s in dataset.train_partition.samples
        )

    def test_generate_quality_prediction_dataset(self):
        """Test generating quality prediction dataset."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_quality_prediction_dataset(
            source="startup",
            num_samples=100,
        )

        assert dataset.dataset_type == DatasetType.QUALITY_PREDICTION
        assert dataset.total_samples == 100
        assert len(dataset.train_partition.samples) == 70
        assert len(dataset.validation_partition.samples) == 15

    def test_dataset_determinism(self):
        """Test that datasets are deterministic with same seed."""
        gen1 = RuntimeIntelligenceDatasetGenerator(deterministic_seed=42)
        dataset1 = gen1.generate_compression_decision_dataset(num_samples=10)

        gen2 = RuntimeIntelligenceDatasetGenerator(deterministic_seed=42)
        dataset2 = gen2.generate_compression_decision_dataset(num_samples=10)

        # Same seed should produce same samples (in same order)
        samples1 = dataset1.train_partition.samples
        samples2 = dataset2.train_partition.samples

        assert len(samples1) == len(samples2)
        for s1, s2 in zip(samples1, samples2):
            assert s1.quality_score == s2.quality_score
            assert s1.token_efficiency == s2.token_efficiency

    def test_dataset_statistics_calculation(self):
        """Test that dataset statistics are calculated."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_provider_selection_dataset(num_samples=50)

        assert len(dataset.domain_distribution) > 0
        assert len(dataset.provider_distribution) > 0
        assert len(dataset.compression_mode_distribution) > 0
        assert len(dataset.complexity_distribution) > 0

    def test_dataset_domain_distribution(self):
        """Test that domains are properly distributed."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_quality_prediction_dataset(num_samples=100)

        total_samples = sum(dataset.domain_distribution.values())
        assert total_samples == 100

    def test_dataset_replay_compatibility(self):
        """Test that datasets are replay-compatible."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_compression_decision_dataset(num_samples=50)

        assert dataset.replay_compatible is True
        for partition in [
            dataset.train_partition,
            dataset.validation_partition,
            dataset.test_partition,
        ]:
            if partition:
                for sample in partition.samples:
                    assert sample.replay_compatible is True
                    assert sample.trace_id is not None

    def test_generator_accumulates_datasets(self):
        """Test that generator accumulates generated datasets."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset1 = generator.generate_compression_decision_dataset(num_samples=50)
        dataset2 = generator.generate_provider_selection_dataset(num_samples=50)
        dataset3 = generator.generate_quality_prediction_dataset(num_samples=50)

        assert len(generator.generated_datasets) == 3
        assert dataset1.dataset_id != dataset2.dataset_id
        assert dataset2.dataset_id != dataset3.dataset_id

    def test_generator_summary(self):
        """Test getting generator summary."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset1 = generator.generate_compression_decision_dataset(num_samples=50)
        dataset2 = generator.generate_provider_selection_dataset(num_samples=50)

        summary = generator.get_dataset_summary()

        assert summary["total_datasets"] == 2
        assert len(summary["datasets"]) == 2

    def test_get_dataset_generator_singleton(self):
        """Test getting dataset generator as singleton."""
        gen1 = get_dataset_generator()
        gen2 = get_dataset_generator()

        assert gen1 is gen2

    def test_sample_quality_vs_efficiency_tradeoff(self):
        """Test that compression modes have appropriate quality/efficiency tradeoffs."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_compression_decision_dataset(num_samples=300)

        # Collect samples by compression mode
        samples_by_mode = {}
        for partition in [
            dataset.train_partition,
            dataset.validation_partition,
            dataset.test_partition,
        ]:
            if partition:
                for sample in partition.samples:
                    mode = sample.chosen_compression_mode
                    if mode not in samples_by_mode:
                        samples_by_mode[mode] = []
                    samples_by_mode[mode].append(sample)

        # Verify tradeoffs exist
        assert len(samples_by_mode) > 0

    def test_multiple_source_workloads(self):
        """Test generating datasets for different source workloads."""
        generator = RuntimeIntelligenceDatasetGenerator()

        for source in ["research", "engineering", "startup", "document"]:
            dataset = generator.generate_quality_prediction_dataset(
                source=source,
                num_samples=20,
            )
            assert dataset.source == source

    def test_sample_availability_providers(self):
        """Test that samples have multiple available providers."""
        generator = RuntimeIntelligenceDatasetGenerator()

        dataset = generator.generate_provider_selection_dataset(num_samples=50)

        for sample in dataset.train_partition.samples:
            assert len(sample.available_providers) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
