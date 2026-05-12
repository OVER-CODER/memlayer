#!/usr/bin/env python3
"""
Infrastructure Validation & Runtime Stabilization Campaign.

Runs end-to-end runtime validation, replay determinism checks, long-horizon
stress campaigns, provider robustness analysis, telemetry consistency checks,
failure injection, dataset determinism checks, and scalability validation.

Outputs structured JSON reports to:
  benchmarks/phase5_history/validation_campaign_<timestamp>/
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional
from unittest.mock import Mock
import hashlib
import json
import random
import subprocess
import sys

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = ROOT / "memlayer-backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.compiler.adaptive_assembly_pipeline import AdaptiveAssemblyPipeline
from app.compiler.adaptive_compilation import RelevanceRankingService
from app.runtime import (
    IntegratedRuntimeSystem,
    LongHorizonStressHarness,
    StressScenario,
    WorkspaceSimulator,
    RuntimeIntelligenceDatasetGenerator,
    RuntimeDiagnosticsDashboard,
    RegressionReplaySuite,
)
from app.runtime.replay_engine import ReplayableTrace
from app.runtime.evolution_tracker import EvolutionMetric
from app.telemetry import (
    get_trace_service,
    get_token_analytics,
    get_latency_profiler,
    get_drift_analyzer,
    get_benchmarking_service,
)


@dataclass
class SyntheticMemory:
    id: str
    raw_content: str
    importance_score: float
    timestamp: datetime
    embedding: List[float]

    def __str__(self) -> str:
        return self.raw_content


def stable_digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()[:16]


class ObjectMemoryStressHarness(LongHorizonStressHarness):
    """Stress harness variant that generates object memories for real pipeline runs."""

    def __init__(self, runtime_system: IntegratedRuntimeSystem):
        super().__init__(runtime_system)
        self._mem_counter = 0

    def _generate_initial_memories(self, count: int) -> List[SyntheticMemory]:
        topics = [
            "machine learning",
            "software engineering",
            "runtime telemetry",
            "semantic continuity",
            "provider behavior",
            "memory hierarchy",
        ]
        memories: List[SyntheticMemory] = []
        for _ in range(count):
            self._mem_counter += 1
            topic = topics[self._mem_counter % len(topics)]
            base = (
                f"Memory {self._mem_counter} about {topic}. "
                f"Runtime note {self._mem_counter % 17}. "
                f"Continuity marker {self._mem_counter % 13}."
            )
            memory = SyntheticMemory(
                id=f"stress-mem-{self._mem_counter:06d}",
                raw_content=base,
                importance_score=0.4 + ((self._mem_counter % 6) * 0.1),
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=self._mem_counter % 90),
                embedding=[float((self._mem_counter + i) % 100) / 100.0 for i in range(32)],
            )
            memories.append(memory)
        return memories

    def _add_memory_noise(
        self, memories: List[SyntheticMemory], noise_level: float
    ) -> List[SyntheticMemory]:
        duplicated = list(memories)
        if not duplicated:
            return duplicated
        num_to_duplicate = max(0, int(len(duplicated) * noise_level * 0.1))
        for _ in range(num_to_duplicate):
            source = duplicated[random.randint(0, len(duplicated) - 1)]
            self._mem_counter += 1
            duplicated.append(
                SyntheticMemory(
                    id=f"stress-mem-{self._mem_counter:06d}",
                    raw_content=f"{source.raw_content} [noisy-dup-{self._mem_counter}]",
                    importance_score=max(0.1, source.importance_score * 0.85),
                    timestamp=source.timestamp,
                    embedding=source.embedding[:],
                )
            )
        return duplicated


class ValidationCampaign:
    def __init__(self):
        random.seed(42)
        np.random.seed(42)

        self.timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.output_dir = (
            BACKEND_ROOT / "benchmarks" / "phase5_history" / f"validation_campaign_{self.timestamp}"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        ranking_service = RelevanceRankingService(Mock())
        pipeline = AdaptiveAssemblyPipeline(
            ranking_service=ranking_service,
            embedding_service=Mock(),
            compression_mode="balanced",
        )
        self.runtime = IntegratedRuntimeSystem(pipeline)
        self.stress_harness = ObjectMemoryStressHarness(self.runtime)
        self.workspace_simulator = WorkspaceSimulator()
        self.dataset_generator = RuntimeIntelligenceDatasetGenerator(deterministic_seed=42)
        self.regression_suite = RegressionReplaySuite(replay_engine=self.runtime.replay_engine)
        self.dashboard = RuntimeDiagnosticsDashboard(
            integrated_runtime=self.runtime,
            stress_harness=self.stress_harness,
        )

        self.trace_service = get_trace_service()
        self.token_analytics = get_token_analytics()
        self.latency_profiler = get_latency_profiler()
        self.drift_analyzer = get_drift_analyzer()
        self.benchmarking_service = get_benchmarking_service()
        self.replay_engine = self.runtime.replay_engine
        self.failure_detector = self.runtime.failure_detector
        self.evolution_tracker = self.runtime.evolution_tracker

    def create_memories(self, count: int, domain: str = "general") -> List[SyntheticMemory]:
        memories: List[SyntheticMemory] = []
        for idx in range(count):
            content = (
                f"[{domain}] Memory {idx} on semantic runtime continuity, "
                f"token behavior, provider adaptation, and replay determinism."
            )
            memories.append(
                SyntheticMemory(
                    id=f"{domain}-mem-{idx:05d}",
                    raw_content=content,
                    importance_score=0.5 + ((idx % 5) * 0.1),
                    timestamp=datetime.now(timezone.utc) - timedelta(minutes=idx % 120),
                    embedding=[float((idx + dim) % 97) / 97.0 for dim in range(32)],
                )
            )
        return memories

    def run_end_to_end_runtime_validation(self) -> Dict[str, Any]:
        queries = [
            ("general", "Explain semantic continuity under adaptive token constraints."),
            ("reasoning", "Why does provider-aware compression affect downstream quality?"),
            ("coding", "Design a deterministic replay validation strategy for context compilation."),
            ("research", "Synthesize tradeoffs between compression ratio and semantic retention."),
            ("narrative", "Summarize runtime evolution over long-horizon workloads."),
        ]
        providers = ["claude", "openai", "gemini"]
        token_budgets = [1200, 2500, 4000]

        run_records: List[Dict[str, Any]] = []
        for idx, (query_type, query) in enumerate(queries):
            memories = self.create_memories(45 + idx * 5, domain=query_type)
            for provider in providers:
                for budget in token_budgets:
                    trace = self.runtime.execute_with_telemetry(
                        query=query,
                        memories=memories,
                        token_budget=budget,
                        provider=provider,
                        compression_mode="balanced",
                        query_type=query_type,
                    )
                    run_records.append(
                        {
                            "trace_id": trace.trace_id,
                            "success": trace.success,
                            "provider": provider,
                            "query_type": query_type,
                            "token_budget": budget,
                            "quality_score": trace.quality_score,
                            "semantic_retention": trace.semantic_retention,
                            "token_efficiency": trace.token_efficiency,
                            "duration_ms": trace.total_duration_ms,
                            "compiled_digest": stable_digest(
                                trace.assembly_result.compiled_context
                                if trace.assembly_result
                                else ""
                            ),
                        }
                    )

        # Determinism check: execute identical request repeatedly and compare outputs.
        det_memories = self.create_memories(60, domain="determinism")
        det_query = "Validate deterministic assembly behavior across repeated executions."
        deterministic_runs: List[Dict[str, Any]] = []
        for _ in range(3):
            det_trace = self.runtime.execute_with_telemetry(
                query=det_query,
                memories=det_memories,
                token_budget=3000,
                provider="claude",
                compression_mode="balanced",
                query_type="reasoning",
            )
            deterministic_runs.append(
                {
                    "trace_id": det_trace.trace_id,
                    "compiled_digest": stable_digest(
                        det_trace.assembly_result.compiled_context
                        if det_trace.assembly_result
                        else ""
                    ),
                    "quality_score": det_trace.quality_score,
                    "semantic_retention": det_trace.semantic_retention,
                    "token_efficiency": det_trace.token_efficiency,
                }
            )

        digests = {run["compiled_digest"] for run in deterministic_runs}
        runtime_stats = self.runtime.get_runtime_statistics()
        report = {
            "executions": len(run_records),
            "successful_executions": sum(1 for item in run_records if item["success"]),
            "run_records": run_records,
            "determinism_check": {
                "runs": deterministic_runs,
                "compiled_context_stable": len(digests) == 1,
                "unique_compiled_digests": len(digests),
            },
            "runtime_statistics": runtime_stats,
        }
        self._write_json("runtime_stability.json", report)
        return report

    def run_recursive_replay_determinism_validation(self) -> Dict[str, Any]:
        stored = list(self.replay_engine.stored_traces.values())
        sampled = stored[: min(40, len(stored))]
        replay_cycles: List[Dict[str, Any]] = []
        divergence_count = 0

        for trace in sampled:
            integrity = self.replay_engine.validate_trace_integrity(trace.trace_id)
            cycle_results = []
            for cycle_idx in range(5):
                result = self.replay_engine.simulate_replay(
                    trace.trace_id,
                    perturbation_factor=0.0,
                )
                cycle_results.append(
                    {
                        "cycle": cycle_idx + 1,
                        "fidelity_score": result.fidelity_score,
                        "quality_diff": result.quality_score_diff,
                        "semantic_diff": result.semantic_retention_diff,
                        "efficiency_diff": result.token_efficiency_diff,
                    }
                )
                if result.fidelity_score < 99.99:
                    divergence_count += 1

            replay_cycles.append(
                {
                    "trace_id": trace.trace_id,
                    "integrity_ok": integrity,
                    "cycles": cycle_results,
                }
            )

        stats = self.replay_engine.get_replay_statistics()
        report = {
            "sampled_traces": len(sampled),
            "divergence_events": divergence_count,
            "replay_statistics": stats,
            "trace_cycles": replay_cycles,
        }
        self._write_json("replay_determinism.json", report)
        return report

    def run_long_horizon_stability_tests(self) -> Dict[str, Any]:
        scenarios = [
            StressScenario(
                scenario_id="long1000",
                scenario_name="Long Horizon 1000 Turn",
                description="1000-turn recursive validation workload",
                num_turns=1000,
                num_memories=35,
                memory_noise_level=0.15,
                recursive_compression_cycles=5,
                provider_switching_frequency=40,
                memory_growth_factor=1.05,
                token_budget=2500,
                token_pressure_level=0.7,
                query_complexity="complex",
                query_diversity=0.8,
            ),
            StressScenario(
                scenario_id="token_pressure_extreme",
                scenario_name="Extreme Token Pressure",
                description="Aggressive token constraints under noisy memory",
                num_turns=300,
                num_memories=70,
                memory_noise_level=0.30,
                recursive_compression_cycles=4,
                provider_switching_frequency=25,
                memory_growth_factor=1.08,
                token_budget=1200,
                token_pressure_level=0.45,
                query_complexity="very_complex",
                query_diversity=0.85,
            ),
        ]

        runs = []
        for idx, scenario in enumerate(scenarios):
            random.seed(42 + idx)
            run = self.stress_harness.run_scenario(scenario)
            runs.append(run.to_dict())

        # Workspace simulations for context evolution under realistic domains
        random.seed(100)
        workspace_runs = []
        ws_defs = [
            self.workspace_simulator.create_research_workspace(num_queries=250),
            self.workspace_simulator.create_software_engineering_workspace(num_queries=250),
            self.workspace_simulator.create_startup_planning_workspace(num_queries=250),
            self.workspace_simulator.create_document_heavy_workspace(num_queries=250),
        ]
        for workspace in ws_defs:
            result = self.workspace_simulator.simulate_workspace(workspace)
            workspace_runs.append(result.to_dict())

        report = {
            "stress_runs": runs,
            "stress_report": self.stress_harness.get_stress_report(),
            "workspace_runs": workspace_runs,
            "workspace_statistics": self.workspace_simulator.get_workspace_statistics(),
        }
        self._write_json("long_horizon_degradation.json", report)
        self._write_json("stress_resilience.json", report["stress_report"])
        return report

    def run_provider_robustness_validation(self) -> Dict[str, Any]:
        traces = [trace for trace in self.runtime.unified_traces if trace.success]
        provider_stats: Dict[str, Dict[str, Any]] = {}
        for provider in ["claude", "openai", "gemini"]:
            provider_traces = [
                trace
                for trace in traces
                if trace.assembly_result and trace.assembly_result.provider == provider
            ]
            if not provider_traces:
                continue
            latencies = [trace.total_duration_ms for trace in provider_traces]
            qualities = [trace.quality_score for trace in provider_traces]
            retentions = [trace.semantic_retention for trace in provider_traces]
            efficiencies = [trace.token_efficiency for trace in provider_traces]
            provider_stats[provider] = {
                "runs": len(provider_traces),
                "avg_latency_ms": mean(latencies),
                "max_latency_ms": max(latencies),
                "latency_variance": float(np.var(latencies)),
                "avg_quality_score": mean(qualities),
                "avg_semantic_retention": mean(retentions),
                "avg_token_efficiency": mean(efficiencies),
            }

        ranking = sorted(
            provider_stats.items(),
            key=lambda item: (
                -item[1]["avg_quality_score"],
                -item[1]["avg_semantic_retention"],
                item[1]["avg_latency_ms"],
            ),
        )

        report = {
            "provider_stats": provider_stats,
            "robustness_ranking": [provider for provider, _ in ranking],
            "benchmark_report": self.benchmarking_service.get_benchmarking_report(),
        }
        self._write_json("provider_robustness.json", report)
        return report

    def run_runtime_regression_campaign(self) -> Dict[str, Any]:
        traces = list(self.replay_engine.stored_traces.values())
        if len(traces) < 10:
            report = {"message": "Insufficient traces for regression campaign", "trace_count": len(traces)}
            self._write_json("regression_analysis.json", report)
            return report

        midpoint = len(traces) // 2
        baseline = traces[:midpoint]
        comparison = traces[midpoint:]

        def to_trace_dict(replayable: ReplayableTrace) -> Dict[str, Any]:
            return {
                "trace_id": replayable.trace_id,
                "query": replayable.query,
                "query_type": replayable.query_type,
                "provider": replayable.provider,
                "compression_mode": replayable.compression_mode,
                "token_budget": replayable.token_budget,
                "memories_count": replayable.memories_count,
                "quality_score": replayable.quality_score,
                "semantic_retention": replayable.semantic_retention,
                "token_efficiency": replayable.token_efficiency,
                "total_duration_ms": replayable.total_duration_ms,
                "token_metrics": replayable.token_metrics,
            }

        baseline_traces = [to_trace_dict(trace) for trace in baseline]
        comparison_traces = [to_trace_dict(trace) for trace in comparison]

        self.regression_suite.register_version_traces("campaign-baseline", baseline_traces)
        self.regression_suite.register_version_traces("campaign-comparison", comparison_traces)
        report = self.regression_suite.compare_versions(
            "campaign-baseline",
            "campaign-comparison",
            report_id="campaign-regression",
        )
        report_dict = report.to_dict()
        self._write_json("regression_analysis.json", report_dict)
        self.regression_suite.export_suite_history(str(self.output_dir / "regression_suite_history.json"))
        return report_dict

    def run_telemetry_consistency_validation(self) -> Dict[str, Any]:
        trace_stats = self.trace_service.get_trace_statistics()
        token_report = self.token_analytics.get_analytics_report()
        latency_report = self.latency_profiler.get_profiler_report()
        drift_report = self.drift_analyzer.get_drift_analyzer_report()
        replay_stats = self.replay_engine.get_replay_statistics()
        runtime_stats = self.runtime.get_runtime_statistics()

        checks = {
            "trace_count_matches_runtime": trace_stats.get("total_traces", 0)
            == runtime_stats.get("total_executions", 0),
            "replay_trace_count_matches_success": replay_stats.get("stored_traces", 0)
            == runtime_stats.get("successful_executions", 0),
            "token_metrics_recorded": token_report.get("total_metrics_recorded", 0)
            == runtime_stats.get("successful_executions", 0),
            "latency_profiles_recorded": latency_report.get("total_profiles", 0)
            == runtime_stats.get("successful_executions", 0),
            "drift_sessions_nonnegative": drift_report.get("statistics", {}).get("total_sessions", 0)
            >= 0,
        }

        report = {
            "checks": checks,
            "all_checks_passed": all(checks.values()),
            "trace_statistics": trace_stats,
            "token_report": token_report,
            "latency_report": latency_report,
            "drift_report": drift_report,
            "replay_statistics": replay_stats,
            "runtime_statistics": runtime_stats,
        }
        self._write_json("telemetry_consistency.json", report)
        return report

    def run_failure_injection_validation(self) -> Dict[str, Any]:
        # synthetic injections
        self.failure_detector.detect_semantic_collapse(
            failure_id="inj-semantic-collapse",
            query="failure injection semantic",
            provider="claude",
            compression_mode="aggressive",
            current_semantic_density=0.35,
            previous_semantic_density=1.0,
            cycle_number=2,
        )
        self.failure_detector.detect_entity_erosion(
            failure_id="inj-entity-erosion",
            query="failure injection entities",
            provider="openai",
            previous_entity_count=100,
            current_entity_count=45,
            current_preservation_ratio=0.45,
            cycle_number=4,
        )
        self.failure_detector.detect_reasoning_continuity_loss(
            failure_id="inj-reasoning-loss",
            query="failure injection reasoning",
            provider="gemini",
            previous_continuity=0.95,
            current_continuity=0.6,
            cycle_number=3,
        )
        self.failure_detector.detect_token_explosion(
            failure_id="inj-token-explosion",
            query="failure injection tokens",
            provider="claude",
            previous_token_count=800,
            current_token_count=2500,
            token_budget=1200,
            cycle_number=5,
        )
        self.failure_detector.detect_allocation_drift(
            failure_id="inj-allocation-drift",
            query="failure injection allocation",
            provider="openai",
            planned_allocation={"reasoning_context": 400, "semantic_memories": 500, "workspace_summary": 300},
            actual_allocation={"reasoning_context": 800, "semantic_memories": 300, "workspace_summary": 100},
            cycle_number=1,
        )

        report = self.failure_detector.get_failure_report()
        self._write_json("failure_propagation.json", report)
        return report

    def run_dataset_validation(self) -> Dict[str, Any]:
        gen_a = RuntimeIntelligenceDatasetGenerator(deterministic_seed=42)
        gen_b = RuntimeIntelligenceDatasetGenerator(deterministic_seed=42)

        dataset_a = gen_a.generate_compression_decision_dataset(source="validation", num_samples=250)
        dataset_b = gen_b.generate_compression_decision_dataset(source="validation", num_samples=250)

        samples_a = [sample.to_dict() for sample in dataset_a.train_partition.samples]
        samples_b = [sample.to_dict() for sample in dataset_b.train_partition.samples]

        stable_checksum_a = stable_digest(samples_a)
        stable_checksum_b = stable_digest(samples_b)

        checksum_report = {
            "generator_checksum_a": dataset_a.get_checksum(),
            "generator_checksum_b": dataset_b.get_checksum(),
            "stable_feature_checksum_a": stable_checksum_a,
            "stable_feature_checksum_b": stable_checksum_b,
            "stable_checksum_match": stable_checksum_a == stable_checksum_b,
        }

        report = {
            "dataset_a": dataset_a.to_dict(),
            "dataset_b": dataset_b.to_dict(),
            "checksum_validation": checksum_report,
            "generator_summary_a": gen_a.get_dataset_summary(),
            "generator_summary_b": gen_b.get_dataset_summary(),
        }
        self._write_json("dataset_validation.json", report)
        return report

    def run_scalability_validation(self) -> Dict[str, Any]:
        scaling_points = [10, 25, 50, 100, 200, 400]
        measurements = []
        for size in scaling_points:
            latencies = []
            efficiencies = []
            retentions = []
            for trial in range(5):
                memories = self.create_memories(size, domain=f"scale-{size}")
                trace = self.runtime.execute_with_telemetry(
                    query=f"Scalability trial {trial} for memory size {size}",
                    memories=memories,
                    token_budget=3000,
                    provider=["claude", "openai", "gemini"][trial % 3],
                    compression_mode="balanced",
                    query_type="research",
                )
                latencies.append(trace.total_duration_ms)
                efficiencies.append(trace.token_efficiency)
                retentions.append(trace.semantic_retention)

            measurements.append(
                {
                    "memory_size": size,
                    "avg_latency_ms": mean(latencies),
                    "max_latency_ms": max(latencies),
                    "avg_token_efficiency": mean(efficiencies),
                    "avg_semantic_retention": mean(retentions),
                }
            )

        report = {
            "scalability_measurements": measurements,
            "latency_growth_curve": [
                {"memory_size": m["memory_size"], "avg_latency_ms": m["avg_latency_ms"]}
                for m in measurements
            ],
        }
        self._write_json("runtime_scalability.json", report)
        return report

    def run_locomo_validation(self) -> Dict[str, Any]:
        dataset_path = ROOT / "Dataset" / "locomo10.json"
        if not dataset_path.exists():
            report = {"status": "missing_dataset", "path": str(dataset_path)}
            self._write_json("locomo_validation.json", report)
            return report

        with open(dataset_path, "r") as file_obj:
            dataset = json.load(file_obj)

        questions = 0
        category_hits: Dict[str, Dict[str, int]] = {}
        hit_at_1 = 0
        hit_at_5 = 0

        for sample in dataset:
            conv = sample.get("conversation", {})
            all_turns = []
            for key, value in conv.items():
                if key.startswith("session_") and isinstance(value, list):
                    all_turns.extend(value)
            dia_lookup = {
                turn.get("dia_id"): turn.get("text", "")
                for turn in all_turns
                if isinstance(turn, dict)
            }
            for qa in sample.get("qa", []):
                questions += 1
                question = qa.get("question", "").lower()
                evidence = qa.get("evidence", [])
                category = str(qa.get("category", "unknown"))
                category_hits.setdefault(category, {"total": 0, "hit_at_5": 0})
                category_hits[category]["total"] += 1

                scored = []
                q_tokens = set(question.split())
                for dia_id, text in dia_lookup.items():
                    tokens = set(text.lower().split())
                    overlap = len(q_tokens.intersection(tokens))
                    scored.append((dia_id, overlap))
                scored.sort(key=lambda item: item[1], reverse=True)
                top1 = [item[0] for item in scored[:1]]
                top5 = [item[0] for item in scored[:5]]

                if any(e in top1 for e in evidence):
                    hit_at_1 += 1
                if any(e in top5 for e in evidence):
                    hit_at_5 += 1
                    category_hits[category]["hit_at_5"] += 1

        report = {
            "dataset_path": str(dataset_path),
            "samples": len(dataset),
            "total_questions": questions,
            "lexical_recall_at_1": (hit_at_1 / questions) if questions else 0.0,
            "lexical_recall_at_5": (hit_at_5 / questions) if questions else 0.0,
            "category_breakdown": category_hits,
        }
        self._write_json("locomo_validation.json", report)
        return report

    def run_pytest_validation(self) -> Dict[str, Any]:
        cmd = [sys.executable, "-m", "pytest", "-q"]
        process = subprocess.run(
            cmd,
            cwd=str(BACKEND_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        report = {
            "command": " ".join(cmd),
            "return_code": process.returncode,
            "stdout_tail": process.stdout[-12000:],
            "stderr_tail": process.stderr[-4000:],
            "passed": process.returncode == 0,
        }
        self._write_json("pytest_validation.json", report)
        return report

    def export_service_reports(self) -> Dict[str, str]:
        exports = {
            "integrated_runtime": str(self.output_dir / "integrated_runtime_report.json"),
            "replay_data": str(self.output_dir / "replay_data.json"),
            "token_analytics": str(self.output_dir / "token_analytics.json"),
            "latency_profiles": str(self.output_dir / "latency_profiles.json"),
            "semantic_drift": str(self.output_dir / "semantic_drift.json"),
            "provider_benchmarks": str(self.output_dir / "provider_benchmarks.json"),
            "failure_report": str(self.output_dir / "failure_report.json"),
            "stress_report": str(self.output_dir / "stress_report.json"),
            "diagnostics_snapshot": str(self.output_dir / "diagnostics_snapshot.json"),
            "diagnostics_console": str(self.output_dir / "diagnostics_console.txt"),
        }

        self.runtime.export_integrated_report(exports["integrated_runtime"])
        self.replay_engine.export_replay_data(exports["replay_data"])
        self.token_analytics.export_analytics(exports["token_analytics"])
        self.latency_profiler.export_profiles(exports["latency_profiles"])
        self.drift_analyzer.export_sessions(exports["semantic_drift"])
        self.benchmarking_service.export_benchmarks(exports["provider_benchmarks"])
        self.failure_detector.export_failures(exports["failure_report"])
        self.stress_harness.export_stress_results(exports["stress_report"])
        snapshot = self.dashboard.capture_snapshot(snapshot_id=f"diag-{self.timestamp}")
        self.dashboard.export_snapshot(snapshot, exports["diagnostics_snapshot"])
        self.dashboard.export_console_report(snapshot, exports["diagnostics_console"])
        return exports

    def run(self) -> Dict[str, Any]:
        runtime_stability = self.run_end_to_end_runtime_validation()
        replay_determinism = self.run_recursive_replay_determinism_validation()
        long_horizon = self.run_long_horizon_stability_tests()
        provider_robustness = self.run_provider_robustness_validation()
        regression_analysis = self.run_runtime_regression_campaign()
        telemetry_consistency = self.run_telemetry_consistency_validation()
        failure_propagation = self.run_failure_injection_validation()
        dataset_validation = self.run_dataset_validation()
        scalability = self.run_scalability_validation()
        locomo_validation = self.run_locomo_validation()
        pytest_validation = self.run_pytest_validation()
        exports = self.export_service_reports()

        summary = {
            "campaign_timestamp": self.timestamp,
            "output_dir": str(self.output_dir),
            "runtime_stability": {
                "executions": runtime_stability.get("executions", 0),
                "successful_executions": runtime_stability.get("successful_executions", 0),
                "determinism_passed": runtime_stability.get("determinism_check", {}).get(
                    "compiled_context_stable", False
                ),
            },
            "replay_determinism": {
                "divergence_events": replay_determinism.get("divergence_events", 0),
                "avg_fidelity": replay_determinism.get("replay_statistics", {}).get(
                    "avg_fidelity_score", 0.0
                ),
            },
            "semantic_continuity": {
                "avg_stress_stability_score": long_horizon.get("stress_report", {}).get(
                    "avg_stability_score", 0.0
                ),
                "avg_workspace_continuity": long_horizon.get("workspace_statistics", {}).get(
                    "avg_cognitive_continuity", 0.0
                ),
            },
            "provider_robustness": provider_robustness.get("robustness_ranking", []),
            "telemetry_consistency_passed": telemetry_consistency.get("all_checks_passed", False),
            "regression_overall_status": (
                regression_analysis.get("comparison", {}).get("recommendation")
                if isinstance(regression_analysis, dict)
                else "unknown"
            ),
            "failure_events_recorded": failure_propagation.get("total_failures", 0),
            "dataset_determinism_passed": dataset_validation.get("checksum_validation", {}).get(
                "stable_checksum_match", False
            ),
            "scalability_points": len(scalability.get("scalability_measurements", [])),
            "locomo_questions": locomo_validation.get("total_questions", 0),
            "pytest_passed": pytest_validation.get("passed", False),
            "exports": exports,
        }

        self._write_json("campaign_summary.json", summary)
        return summary

    def _write_json(self, name: str, payload: Dict[str, Any]) -> None:
        with open(self.output_dir / name, "w") as file_obj:
            json.dump(payload, file_obj, indent=2, default=str)


def main() -> int:
    campaign = ValidationCampaign()
    summary = campaign.run()
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
