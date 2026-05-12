"""
Long-Horizon Stress Harness for Phase 5B.

Simulates realistic long-running workloads to stress-test the runtime:
- 1000+ turn conversations
- Recursive compression cycles
- Memory saturation scenarios
- Noisy memory environments
- Mixed-domain cognition
- Large semantic memory pools

Tracks:
- Semantic degradation
- Runtime stability
- Token efficiency evolution
- Provider adaptation
- Emergent failures
"""

from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
import random
import uuid

from app.runtime import (
    UnifiedCognitionTrace,
    IntegratedRuntimeSystem,
    get_failure_detector,
)

logger = logging.getLogger(__name__)


@dataclass
class StressScenario:
    """Definition of a stress test scenario."""

    scenario_id: str
    scenario_name: str
    description: str

    # Parameters
    num_turns: int = 100
    num_memories: int = 50
    memory_noise_level: float = 0.0  # 0-1, how noisy/mixed-domain
    recursive_compression_cycles: int = 1
    provider_switching_frequency: int = 0  # 0 = never, >0 = every N turns
    memory_growth_factor: float = 1.0  # Multiply memory pool each cycle

    # Token pressure
    token_budget: int = 4000
    token_pressure_level: float = 0.8  # 0-1, how tight the budget is

    # Query characteristics
    query_complexity: str = "moderate"  # simple, moderate, complex, very_complex
    query_diversity: float = 0.5  # 0-1, how varied queries are

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "description": self.description,
            "num_turns": self.num_turns,
            "num_memories": self.num_memories,
            "memory_noise_level": self.memory_noise_level,
            "recursive_compression_cycles": self.recursive_compression_cycles,
            "provider_switching_frequency": self.provider_switching_frequency,
            "memory_growth_factor": self.memory_growth_factor,
            "token_budget": self.token_budget,
            "token_pressure_level": self.token_pressure_level,
            "query_complexity": self.query_complexity,
            "query_diversity": self.query_diversity,
        }


@dataclass
class StressTestRun:
    """Results of a stress test run."""

    run_id: str
    scenario: StressScenario
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Execution
    total_turns: int = 0
    successful_turns: int = 0
    failed_turns: int = 0

    # Quality metrics
    avg_quality_score: float = 0.0
    min_quality_score: float = 1.0
    quality_degradation_rate: float = 0.0

    # Semantic metrics
    avg_semantic_retention: float = 0.0
    semantic_retention_degradation: float = 0.0

    # Token metrics
    avg_token_efficiency: float = 0.0
    token_efficiency_trend: List[float] = field(default_factory=list)
    max_tokens_used: int = 0

    # Runtime stability
    crashes_detected: int = 0
    provider_failures: Dict[str, int] = field(default_factory=dict)
    failure_patterns: List[str] = field(default_factory=list)

    # Performance
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0

    # Resilience
    recovery_attempts: int = 0
    recovery_successes: int = 0
    recovery_rate: float = 0.0

    # Overall assessment
    stability_score: float = 0.0  # 0-100
    stress_level_tolerated: str = "unknown"  # low, moderate, high, critical

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "run_id": self.run_id,
            "scenario": self.scenario.to_dict(),
            "timestamp": self.timestamp.isoformat(),
            "total_turns": self.total_turns,
            "successful_turns": self.successful_turns,
            "failed_turns": self.failed_turns,
            "success_rate": (
                self.successful_turns / self.total_turns
                if self.total_turns > 0
                else 0.0
            ),
            "avg_quality_score": self.avg_quality_score,
            "min_quality_score": self.min_quality_score,
            "quality_degradation_rate": self.quality_degradation_rate,
            "avg_semantic_retention": self.avg_semantic_retention,
            "semantic_retention_degradation": self.semantic_retention_degradation,
            "avg_token_efficiency": self.avg_token_efficiency,
            "max_tokens_used": self.max_tokens_used,
            "crashes_detected": self.crashes_detected,
            "provider_failures": self.provider_failures,
            "failure_patterns": self.failure_patterns,
            "avg_latency_ms": self.avg_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "recovery_rate": self.recovery_rate,
            "stability_score": self.stability_score,
            "stress_level_tolerated": self.stress_level_tolerated,
        }


class LongHorizonStressHarness:
    """
    Stress testing framework for long-running workloads.

    Simulates realistic scenarios to identify:
    - Degradation patterns
    - Runtime instability
    - Provider-specific failures
    - Emergent failure conditions
    """

    def __init__(self, runtime_system: IntegratedRuntimeSystem):
        """
        Initialize stress harness.

        Args:
            runtime_system: IntegratedRuntimeSystem to stress test
        """
        self.runtime = runtime_system
        self.failure_detector = get_failure_detector()

        # Results storage
        self.test_runs: List[StressTestRun] = []

        logger.info("Long-Horizon Stress Harness initialized")

    def run_scenario(self, scenario: StressScenario) -> StressTestRun:
        """
        Execute a stress test scenario.

        Args:
            scenario: Stress scenario definition

        Returns:
            StressTestRun with results
        """
        run_id = f"stress-{scenario.scenario_id[:8]}"
        test_run = StressTestRun(
            run_id=run_id,
            scenario=scenario,
        )

        logger.info(
            f"Starting stress test {run_id}: {scenario.scenario_name} "
            f"({scenario.num_turns} turns, "
            f"{scenario.num_memories} memories)"
        )

        quality_scores = []
        semantic_retentions = []
        latencies = []
        token_counts = []
        previous_quality = 1.0

        providers = ["claude", "openai", "gemini"]
        current_provider_idx = 0
        memory_pool = self._generate_initial_memories(scenario.num_memories)

        for turn in range(scenario.num_turns):
            try:
                # Generate query based on complexity
                query = self._generate_query(
                    scenario.query_complexity, scenario.query_diversity, turn
                )

                # Add noise to memory pool
                if scenario.memory_noise_level > 0:
                    memory_pool = self._add_memory_noise(
                        memory_pool, scenario.memory_noise_level
                    )

                # Potentially switch provider
                if (
                    scenario.provider_switching_frequency > 0
                    and turn % scenario.provider_switching_frequency == 0
                ):
                    current_provider_idx = (current_provider_idx + 1) % len(providers)

                provider = providers[current_provider_idx]

                # Adjusted token budget based on pressure
                actual_token_budget = int(
                    scenario.token_budget * scenario.token_pressure_level
                )

                # Execute with telemetry
                unified_trace = self.runtime.execute_with_telemetry(
                    query=query,
                    memories=memory_pool[: scenario.num_memories],
                    token_budget=actual_token_budget,
                    provider=provider,
                    compression_mode="balanced",
                    query_type=scenario.query_complexity,
                )

                if unified_trace.success:
                    test_run.successful_turns += 1

                    # Record metrics
                    quality_scores.append(unified_trace.quality_score)
                    semantic_retentions.append(unified_trace.semantic_retention)
                    latencies.append(unified_trace.total_duration_ms)
                    token_counts.append(
                        unified_trace.token_metrics.compressed_tokens_output
                        if unified_trace.token_metrics
                        else 0
                    )

                    # Detect degradation
                    degradation = previous_quality - unified_trace.quality_score
                    if degradation > 0.05:
                        self.failure_detector.detect_semantic_collapse(
                            failure_id=f"degrad-{turn}",
                            query=query,
                            provider=provider,
                            compression_mode="balanced",
                            current_semantic_density=unified_trace.semantic_retention,
                            previous_semantic_density=previous_quality,
                            cycle_number=turn,
                        )

                    previous_quality = unified_trace.quality_score

                else:
                    test_run.failed_turns += 1
                    if provider not in test_run.provider_failures:
                        test_run.provider_failures[provider] = 0
                    test_run.provider_failures[provider] += 1

                # Grow memory pool for recursive cycles
                if (
                    turn % (scenario.num_turns // scenario.recursive_compression_cycles)
                    == 0
                    and turn > 0
                ):
                    growth = int(
                        len(memory_pool) * (scenario.memory_growth_factor - 1.0)
                    )
                    if growth > 0:
                        memory_pool.extend(self._generate_initial_memories(growth))

            except Exception as e:
                logger.error(f"Turn {turn} crashed: {e}", exc_info=True)
                test_run.crashes_detected += 1
                test_run.failed_turns += 1

        # Calculate final metrics
        test_run.total_turns = scenario.num_turns

        if quality_scores:
            test_run.avg_quality_score = sum(quality_scores) / len(quality_scores)
            test_run.min_quality_score = min(quality_scores)
            test_run.quality_degradation_rate = (
                (quality_scores[0] - quality_scores[-1]) / quality_scores[0]
                if quality_scores[0] > 0
                else 0.0
            )

        if semantic_retentions:
            test_run.avg_semantic_retention = sum(semantic_retentions) / len(
                semantic_retentions
            )
            test_run.semantic_retention_degradation = (
                (semantic_retentions[0] - semantic_retentions[-1])
                / semantic_retentions[0]
                if semantic_retentions[0] > 0
                else 0.0
            )

        if token_counts:
            test_run.max_tokens_used = max(token_counts)

        if latencies:
            test_run.avg_latency_ms = sum(latencies) / len(latencies)
            sorted_latencies = sorted(latencies)
            test_run.p95_latency_ms = sorted_latencies[
                int(len(sorted_latencies) * 0.95)
            ]
            test_run.p99_latency_ms = sorted_latencies[
                int(len(sorted_latencies) * 0.99)
            ]

        # Calculate stability score
        success_rate = (
            test_run.successful_turns / test_run.total_turns
            if test_run.total_turns > 0
            else 0.0
        )
        quality_component = test_run.avg_quality_score * 30
        stability_component = success_rate * 40
        degradation_component = (1.0 - test_run.quality_degradation_rate) * 30

        test_run.stability_score = (
            quality_component + stability_component + degradation_component
        )

        # Classify stress tolerance
        if test_run.stability_score >= 85 and test_run.crashes_detected == 0:
            test_run.stress_level_tolerated = "high"
        elif test_run.stability_score >= 70:
            test_run.stress_level_tolerated = "moderate"
        else:
            test_run.stress_level_tolerated = "low"

        self.test_runs.append(test_run)

        logger.info(
            f"Stress test {run_id} complete: "
            f"success_rate={success_rate * 100:.1f}%, "
            f"stability_score={test_run.stability_score:.1f}, "
            f"stress_tolerance={test_run.stress_level_tolerated}"
        )

        return test_run

    def _generate_initial_memories(self, count: int) -> List[str]:
        """Generate initial memory pool."""
        topics = [
            "machine learning",
            "software engineering",
            "climate science",
            "medical research",
            "finance",
            "history",
            "biology",
            "physics",
        ]

        memories = []
        for i in range(count):
            topic = random.choice(topics)
            memory = f"Memory {i}: {topic} context {random.randint(0, 1000)}"
            memories.append(memory)

        return memories

    def _add_memory_noise(self, memories: List[str], noise_level: float) -> List[str]:
        """Add noise/redundancy to memory pool."""
        num_to_duplicate = int(len(memories) * noise_level * 0.1)
        for _ in range(num_to_duplicate):
            idx = random.randint(0, len(memories) - 1)
            # Duplicate with slight modification
            memories.append(memories[idx] + " (duplicate)")

        return memories

    def _generate_query(self, complexity: str, diversity: float, turn: int) -> str:
        """Generate query based on complexity and diversity."""
        queries = {
            "simple": [
                "What is X?",
                "Define Y.",
                "Explain Z.",
            ],
            "moderate": [
                "How does X relate to Y in the context of Z?",
                "Explain the process of X and its implications for Y.",
                "Compare X and Y approaches to problem Z.",
            ],
            "complex": [
                "Provide a detailed analysis of X's impact on Y, considering Z factors and historical trends.",
                "Synthesize findings from X, Y, and Z to propose a novel approach.",
                "Critically evaluate X's effectiveness in Y domain, with implications for Z.",
            ],
            "very_complex": [
                "Given the multi-faceted nature of X, how would you design a system integrating Y and Z while accounting for emerging challenges?",
                "Provide a comprehensive framework for X that synthesizes perspectives from Y, Z, and related fields.",
                "Design an adaptive strategy for X that responds to Y dynamics while preserving Z principles.",
            ],
        }

        base_queries = queries.get(complexity, queries["moderate"])

        # Add diversity by varying queries
        if random.random() < diversity:
            return base_queries[random.randint(0, len(base_queries) - 1)]
        else:
            # Repeat similar query
            return base_queries[turn % len(base_queries)]

    def get_stress_report(self) -> Dict:
        """Generate comprehensive stress test report."""
        if not self.test_runs:
            return {"message": "No stress tests run"}

        avg_stability = (
            sum(r.stability_score for r in self.test_runs) / len(self.test_runs)
            if self.test_runs
            else 0.0
        )

        total_turns = sum(r.total_turns for r in self.test_runs)
        total_successful = sum(r.successful_turns for r in self.test_runs)

        return {
            "total_runs": len(self.test_runs),
            "total_turns_executed": total_turns,
            "overall_success_rate": (
                total_successful / total_turns if total_turns > 0 else 0.0
            ),
            "avg_stability_score": avg_stability,
            "stress_runs": [r.to_dict() for r in self.test_runs[-10:]],
        }

    def export_stress_results(self, output_file: str) -> str:
        """Export stress test results to JSON."""
        report = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "total_runs": len(self.test_runs),
            "stress_report": self.get_stress_report(),
        }

        import json

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Stress test results exported to {output_file}")
        return output_file


# Predefined stress scenarios
def create_standard_stress_scenarios() -> List[StressScenario]:
    """Create standard stress test scenarios."""
    return [
        StressScenario(
            scenario_id="baseline",
            scenario_name="Baseline Stability",
            description="Basic load test with stable parameters",
            num_turns=100,
            num_memories=50,
            memory_noise_level=0.0,
            recursive_compression_cycles=1,
            token_budget=4000,
            token_pressure_level=0.8,
            query_complexity="moderate",
            query_diversity=0.3,
        ),
        StressScenario(
            scenario_id="recursive",
            scenario_name="Recursive Compression Stress",
            description="Multiple compression cycles with growing memory",
            num_turns=200,
            num_memories=50,
            memory_noise_level=0.1,
            recursive_compression_cycles=4,
            memory_growth_factor=1.2,
            token_budget=4000,
            token_pressure_level=0.7,
            query_complexity="complex",
            query_diversity=0.5,
        ),
        StressScenario(
            scenario_id="provider_switching",
            scenario_name="Provider Switching Stress",
            description="Rapid provider switching with mixed query types",
            num_turns=150,
            num_memories=75,
            memory_noise_level=0.15,
            provider_switching_frequency=25,
            token_budget=3000,
            token_pressure_level=0.6,
            query_complexity="very_complex",
            query_diversity=0.8,
        ),
        StressScenario(
            scenario_id="saturation",
            scenario_name="Memory Saturation Stress",
            description="Large memory pools with high compression pressure",
            num_turns=300,
            num_memories=200,
            memory_noise_level=0.3,
            recursive_compression_cycles=3,
            memory_growth_factor=1.5,
            token_budget=2000,
            token_pressure_level=0.4,
            query_complexity="very_complex",
            query_diversity=0.9,
        ),
    ]


# Global stress harness instance
_stress_harness: Optional[LongHorizonStressHarness] = None


def get_stress_harness(
    runtime_system: Optional[IntegratedRuntimeSystem] = None,
) -> LongHorizonStressHarness:
    """Get or create the global stress harness."""
    global _stress_harness
    if _stress_harness is None:
        if runtime_system is None:
            raise ValueError("Runtime system required for first initialization")
        _stress_harness = LongHorizonStressHarness(runtime_system)
    return _stress_harness
