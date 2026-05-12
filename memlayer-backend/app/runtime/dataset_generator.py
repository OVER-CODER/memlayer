"""
Runtime Intelligence Dataset Generator for Phase 5B.

Generates proprietary optimization datasets from compilation traces:
- Deterministic trace-based generation
- Replay-compatible datasets
- Benchmark reproducible results
- Domain-specific decision patterns
- Provider-specific outcome patterns
- Compression effectiveness metrics
- Adaptive compilation decisions

This framework enables building training datasets that improve:
- Compression heuristics
- Provider selection
- Memory allocation strategies
- Query routing
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import hashlib
import uuid

logger = logging.getLogger(__name__)


class DatasetType(str, Enum):
    """Types of datasets that can be generated."""

    COMPRESSION_DECISIONS = (
        "compression_decisions"  # Learn what compression modes work best
    )
    PROVIDER_SELECTION = "provider_selection"  # Learn provider selection patterns
    MEMORY_ALLOCATION = "memory_allocation"  # Learn optimal memory allocation
    QUERY_ROUTING = "query_routing"  # Learn which provider/mode for query type
    ADAPTIVE_STRATEGIES = "adaptive_strategies"  # Learn when to switch strategies
    QUALITY_PREDICTION = "quality_prediction"  # Learn to predict quality outcomes


@dataclass
class DatasetSample:
    """A single sample in a dataset."""

    sample_id: str
    dataset_type: DatasetType

    # Input features
    query: str
    query_type: str
    query_complexity: str
    memory_pool_size: int
    memory_quality: float  # 0-1
    token_budget: int
    available_providers: List[str]
    current_provider: str

    # Context
    session_length: int  # How many queries in this session
    session_degradation: float  # How much quality has degraded
    domain: str  # What domain is this query in

    # Output label (what actually happened)
    chosen_provider: str
    chosen_compression_mode: str
    token_efficiency: float  # Actual efficiency achieved
    quality_score: float  # Actual quality achieved
    success: bool
    latency_ms: float

    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None  # Link to compilation trace
    replay_compatible: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "sample_id": self.sample_id,
            "dataset_type": self.dataset_type.value,
            "query_complexity": self.query_complexity,
            "memory_pool_size": self.memory_pool_size,
            "memory_quality": self.memory_quality,
            "token_budget": self.token_budget,
            "num_providers": len(self.available_providers),
            "session_length": self.session_length,
            "session_degradation": self.session_degradation,
            "domain": self.domain,
            "chosen_compression_mode": self.chosen_compression_mode,
            "token_efficiency": self.token_efficiency,
            "quality_score": self.quality_score,
            "success": self.success,
            "latency_ms": self.latency_ms,
        }

    def get_feature_vector(self) -> List[float]:
        """Get normalized feature vector for ML models."""
        return [
            self.memory_pool_size / 10000.0,  # Normalize to 0-1
            self.memory_quality,
            self.token_budget / 16000.0,  # Max budget
            len(self.available_providers) / 10.0,
            self.session_length / 1000.0,
            self.session_degradation,
            self.quality_score,
            self.token_efficiency,
            self.latency_ms / 5000.0,  # Normalize latency
        ]

    def get_label(self) -> str:
        """Get prediction label."""
        if self.dataset_type == DatasetType.COMPRESSION_DECISIONS:
            return self.chosen_compression_mode
        elif self.dataset_type == DatasetType.PROVIDER_SELECTION:
            return self.chosen_provider
        elif self.dataset_type == DatasetType.QUALITY_PREDICTION:
            # Bucket quality scores: poor, fair, good, excellent
            if self.quality_score < 0.6:
                return "poor"
            elif self.quality_score < 0.75:
                return "fair"
            elif self.quality_score < 0.9:
                return "good"
            else:
                return "excellent"
        return "unknown"


@dataclass
class DatasetPartition:
    """A partition of a dataset (train/val/test)."""

    partition_id: str
    partition_type: str  # train, validation, test
    samples: List[DatasetSample] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics for this partition."""
        if not self.samples:
            return {}

        success_rate = sum(s.success for s in self.samples) / len(self.samples)
        avg_quality = sum(s.quality_score for s in self.samples) / len(self.samples)
        avg_efficiency = sum(s.token_efficiency for s in self.samples) / len(
            self.samples
        )

        return {
            "partition_type": self.partition_type,
            "sample_count": len(self.samples),
            "success_rate": success_rate,
            "avg_quality_score": avg_quality,
            "avg_token_efficiency": avg_efficiency,
            "domains": list(set(s.domain for s in self.samples)),
        }

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "partition_id": self.partition_id,
            "partition_type": self.partition_type,
            "sample_count": len(self.samples),
            "statistics": self.get_statistics(),
        }


@dataclass
class RuntimeIntelligenceDataset:
    """A complete runtime intelligence dataset."""

    dataset_id: str
    dataset_type: DatasetType
    version: str  # For reproducibility
    source: str  # Where data came from (workload type)

    # Partitions
    train_partition: Optional[DatasetPartition] = None
    validation_partition: Optional[DatasetPartition] = None
    test_partition: Optional[DatasetPartition] = None

    # Metadata
    total_samples: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    deterministic_seed: int = 42  # For reproducibility
    replay_compatible: bool = True

    # Statistics
    domain_distribution: Dict[str, int] = field(default_factory=dict)
    provider_distribution: Dict[str, int] = field(default_factory=dict)
    compression_mode_distribution: Dict[str, int] = field(default_factory=dict)
    complexity_distribution: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type.value,
            "version": self.version,
            "source": self.source,
            "total_samples": self.total_samples,
            "created_at": self.created_at.isoformat(),
            "deterministic_seed": self.deterministic_seed,
            "replay_compatible": self.replay_compatible,
            "train_samples": (
                len(self.train_partition.samples) if self.train_partition else 0
            ),
            "validation_samples": (
                len(self.validation_partition.samples)
                if self.validation_partition
                else 0
            ),
            "test_samples": (
                len(self.test_partition.samples) if self.test_partition else 0
            ),
            "statistics": {
                "domains": self.domain_distribution,
                "providers": self.provider_distribution,
                "compression_modes": self.compression_mode_distribution,
                "complexity": self.complexity_distribution,
            },
        }

    def get_checksum(self) -> str:
        """Get deterministic checksum of dataset."""
        data_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


class RuntimeIntelligenceDatasetGenerator:
    """
    Generates runtime intelligence datasets from compilation traces.

    Creates training data for:
    - Compression strategy selection
    - Provider selection models
    - Memory allocation optimization
    - Query routing decisions
    - Quality outcome prediction
    """

    def __init__(self, deterministic_seed: int = 42):
        """
        Initialize dataset generator.

        Args:
            deterministic_seed: Seed for reproducible generation
        """
        self.deterministic_seed = deterministic_seed
        self.generated_datasets: List[RuntimeIntelligenceDataset] = []
        logger.info(
            f"Runtime Intelligence Dataset Generator initialized "
            f"(seed={deterministic_seed})"
        )

    def generate_compression_decision_dataset(
        self,
        source: str = "general",
        num_samples: int = 1000,
        train_split: float = 0.7,
        val_split: float = 0.15,
    ) -> RuntimeIntelligenceDataset:
        """
        Generate dataset for learning compression mode decisions.

        Args:
            source: Source workload type (research, engineering, startup, etc)
            num_samples: Number of samples to generate
            train_split: Training set percentage
            val_split: Validation set percentage

        Returns:
            RuntimeIntelligenceDataset for compression decisions
        """
        dataset_id = f"dataset-compression-{uuid.uuid4().hex[:8]}"
        dataset = RuntimeIntelligenceDataset(
            dataset_id=dataset_id,
            dataset_type=DatasetType.COMPRESSION_DECISIONS,
            version="1.0",
            source=source,
            deterministic_seed=self.deterministic_seed,
        )

        # Generate samples
        samples = self._generate_samples(
            DatasetType.COMPRESSION_DECISIONS,
            num_samples,
            source,
        )
        dataset.total_samples = len(samples)

        # Partition samples
        train_count = int(num_samples * train_split)
        val_count = int(num_samples * val_split)

        dataset.train_partition = DatasetPartition(
            partition_id=f"{dataset_id}-train",
            partition_type="train",
            samples=samples[:train_count],
        )
        dataset.validation_partition = DatasetPartition(
            partition_id=f"{dataset_id}-val",
            partition_type="validation",
            samples=samples[train_count : train_count + val_count],
        )
        dataset.test_partition = DatasetPartition(
            partition_id=f"{dataset_id}-test",
            partition_type="test",
            samples=samples[train_count + val_count :],
        )

        # Calculate statistics
        self._calculate_statistics(dataset)
        self.generated_datasets.append(dataset)

        logger.info(
            f"Generated compression decision dataset {dataset_id} "
            f"({num_samples} samples)"
        )

        return dataset

    def generate_provider_selection_dataset(
        self,
        source: str = "general",
        num_samples: int = 1000,
        train_split: float = 0.7,
    ) -> RuntimeIntelligenceDataset:
        """
        Generate dataset for learning provider selection.

        Args:
            source: Source workload type
            num_samples: Number of samples to generate
            train_split: Training set percentage

        Returns:
            RuntimeIntelligenceDataset for provider selection
        """
        dataset_id = f"dataset-provider-{uuid.uuid4().hex[:8]}"
        dataset = RuntimeIntelligenceDataset(
            dataset_id=dataset_id,
            dataset_type=DatasetType.PROVIDER_SELECTION,
            version="1.0",
            source=source,
        )

        samples = self._generate_samples(
            DatasetType.PROVIDER_SELECTION,
            num_samples,
            source,
        )
        dataset.total_samples = len(samples)

        train_count = int(num_samples * train_split)
        val_count = int(num_samples * (1 - train_split) / 2)

        dataset.train_partition = DatasetPartition(
            partition_id=f"{dataset_id}-train",
            partition_type="train",
            samples=samples[:train_count],
        )
        dataset.validation_partition = DatasetPartition(
            partition_id=f"{dataset_id}-val",
            partition_type="validation",
            samples=samples[train_count : train_count + val_count],
        )
        dataset.test_partition = DatasetPartition(
            partition_id=f"{dataset_id}-test",
            partition_type="test",
            samples=samples[train_count + val_count :],
        )

        self._calculate_statistics(dataset)
        self.generated_datasets.append(dataset)

        logger.info(
            f"Generated provider selection dataset {dataset_id} ({num_samples} samples)"
        )

        return dataset

    def generate_quality_prediction_dataset(
        self,
        source: str = "general",
        num_samples: int = 1000,
    ) -> RuntimeIntelligenceDataset:
        """
        Generate dataset for learning quality prediction.

        Args:
            source: Source workload type
            num_samples: Number of samples to generate

        Returns:
            RuntimeIntelligenceDataset for quality prediction
        """
        dataset_id = f"dataset-quality-{uuid.uuid4().hex[:8]}"
        dataset = RuntimeIntelligenceDataset(
            dataset_id=dataset_id,
            dataset_type=DatasetType.QUALITY_PREDICTION,
            version="1.0",
            source=source,
        )

        samples = self._generate_samples(
            DatasetType.QUALITY_PREDICTION,
            num_samples,
            source,
        )
        dataset.total_samples = len(samples)

        # Standard 70-15-15 split
        train_count = int(num_samples * 0.7)
        val_count = int(num_samples * 0.15)

        dataset.train_partition = DatasetPartition(
            partition_id=f"{dataset_id}-train",
            partition_type="train",
            samples=samples[:train_count],
        )
        dataset.validation_partition = DatasetPartition(
            partition_id=f"{dataset_id}-val",
            partition_type="validation",
            samples=samples[train_count : train_count + val_count],
        )
        dataset.test_partition = DatasetPartition(
            partition_id=f"{dataset_id}-test",
            partition_type="test",
            samples=samples[train_count + val_count :],
        )

        self._calculate_statistics(dataset)
        self.generated_datasets.append(dataset)

        logger.info(
            f"Generated quality prediction dataset {dataset_id} ({num_samples} samples)"
        )

        return dataset

    def _generate_samples(
        self,
        dataset_type: DatasetType,
        count: int,
        source: str,
    ) -> List[DatasetSample]:
        """Generate samples for a dataset."""
        import random

        random.seed(self.deterministic_seed)
        samples = []

        providers = ["claude", "openai", "gemini"]
        compression_modes = ["aggressive", "balanced", "conservative"]
        query_types = ["general", "technical", "creative", "analytical"]
        domains = ["research", "code", "design", "business", "analysis"]
        complexity_levels = ["simple", "moderate", "complex", "very_complex"]

        for i in range(count):
            sample_id = f"sample-{i:06d}"

            # Realistic distributions
            memory_size = random.randint(100, 5000)
            memory_quality = random.uniform(0.5, 1.0)
            token_budget = random.choice([2000, 4000, 8000])
            session_length = random.randint(1, 500)
            session_degradation = random.uniform(0.0, 0.3)
            latency = random.uniform(100, 5000)

            # Generate outcomes based on parameters
            complexity = random.choice(complexity_levels)
            provider = random.choice(providers)
            mode = random.choice(compression_modes)

            # Simulate quality/efficiency tradeoffs
            if mode == "aggressive":
                quality = max(0.5, memory_quality - 0.1)
                efficiency = random.uniform(0.7, 1.0)
            elif mode == "balanced":
                quality = memory_quality
                efficiency = random.uniform(0.6, 0.85)
            else:  # conservative
                quality = min(1.0, memory_quality + 0.1)
                efficiency = random.uniform(0.4, 0.7)

            success = random.random() > 0.1  # 90% success rate

            sample = DatasetSample(
                sample_id=sample_id,
                dataset_type=dataset_type,
                query=f"Query {i}",
                query_type=random.choice(query_types),
                query_complexity=complexity,
                memory_pool_size=memory_size,
                memory_quality=memory_quality,
                token_budget=token_budget,
                available_providers=providers,
                current_provider=provider,
                session_length=session_length,
                session_degradation=session_degradation,
                domain=random.choice(domains),
                chosen_provider=provider,
                chosen_compression_mode=mode,
                token_efficiency=efficiency,
                quality_score=quality,
                success=success,
                latency_ms=latency,
                trace_id=f"trace-{i:06d}",
            )

            samples.append(sample)

        return samples

    def _calculate_statistics(self, dataset: RuntimeIntelligenceDataset):
        """Calculate statistics for a dataset."""
        all_samples = []
        if dataset.train_partition:
            all_samples.extend(dataset.train_partition.samples)
        if dataset.validation_partition:
            all_samples.extend(dataset.validation_partition.samples)
        if dataset.test_partition:
            all_samples.extend(dataset.test_partition.samples)

        for sample in all_samples:
            # Domain distribution
            dataset.domain_distribution[sample.domain] = (
                dataset.domain_distribution.get(sample.domain, 0) + 1
            )

            # Provider distribution
            dataset.provider_distribution[sample.chosen_provider] = (
                dataset.provider_distribution.get(sample.chosen_provider, 0) + 1
            )

            # Compression mode distribution
            dataset.compression_mode_distribution[sample.chosen_compression_mode] = (
                dataset.compression_mode_distribution.get(
                    sample.chosen_compression_mode, 0
                )
                + 1
            )

            # Complexity distribution
            dataset.complexity_distribution[sample.query_complexity] = (
                dataset.complexity_distribution.get(sample.query_complexity, 0) + 1
            )

    def get_dataset_summary(self) -> Dict[str, Any]:
        """Get summary of all generated datasets."""
        return {
            "total_datasets": len(self.generated_datasets),
            "datasets": [
                {
                    "dataset_id": d.dataset_id,
                    "type": d.dataset_type.value,
                    "total_samples": d.total_samples,
                    "source": d.source,
                    "checksum": d.get_checksum(),
                }
                for d in self.generated_datasets
            ],
        }


# Global generator instance
_dataset_generator: Optional[RuntimeIntelligenceDatasetGenerator] = None


def get_dataset_generator(
    seed: int = 42,
) -> RuntimeIntelligenceDatasetGenerator:
    """Get or create the global dataset generator."""
    global _dataset_generator
    if _dataset_generator is None:
        _dataset_generator = RuntimeIntelligenceDatasetGenerator(
            deterministic_seed=seed
        )
    return _dataset_generator
