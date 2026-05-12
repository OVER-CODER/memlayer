# Phase 6.5 — Cross-Layer Runtime Evaluation & Optimization

## Objective
Phase 6.5 validates emergent behavior across the integrated cognition stack instead of isolated subsystem behavior.

Validated stack:
- Workspace semantic state
- Adaptive semantic compiler runtime
- View Engine Compiler projections
- Replay and determinism systems
- Diagnostics and telemetry aggregation

## Implemented Components

### 1. CrossLayerEvaluationFramework
File: `app/runtime/cross_layer_evaluation.py`

Core responsibilities:
- end-to-end runtime stack evaluation
- semantic fidelity analysis
- cross-view consistency analysis
- replay integrity stress validation
- long-horizon projection evolution tracking
- token economics evaluation
- provider divergence analysis
- optimization recommendation generation

Primary output:
- `CrossLayerEvaluationReport` (JSON-serializable)

### 2. Semantic Fidelity Suite
Measured per report:
- semantic preservation
- reasoning continuity
- entity preservation
- context integrity
- degradation index

### 3. Cross-View Consistency Tooling
Measured per report:
- overlap matrix
- divergence matrix
- average overlap/divergence
- over-divergence detection
- over-redundancy detection
- context fragmentation risk

### 4. Replay Integrity Stress Suite
Measured per report:
- deterministic checks/mismatches
- determinism rate
- provider-level replay breakdown
- drift alerts for nondeterministic outputs

### 5. Projection Evolution Tracker
Measured per report:
- stepwise projection timeline
- average/max drift
- semantic erosion
- provider token-efficiency evolution

### 6. Provider Divergence Analysis
Measured per report:
- divergence by view type
- provider quality spread
- adaptation heatmap
- provider robustness ranking

### 7. Token Economics Evaluator
Measured per report:
- average token budget used
- projection token density
- semantic value per token
- provider and view token efficiency
- redundant projection overhead

## Unified Diagnostics Expansion
File: `app/runtime/diagnostics_dashboard.py`

Runtime diagnostics snapshots now support optional cross-layer attachment via `cross_layer_framework`.

New snapshot field:
- `cross_layer_diagnostics`

Dashboard can now display:
- latest cross-layer report id
- cross-layer determinism rate
- cross-layer semantic preservation

## Benchmarks
Benchmark runner:
- `benchmarks/phase6_5_cross_layer/run_cross_layer_campaign.py`

Campaign characteristics:
- multiple workloads (`research`, `drafting`, `tooling`, `critique`)
- all core providers (`claude`, `openai`, `gemini`)
- replay cycles + evolution steps
- persisted JSON outputs:
  - per-workload rows
  - summary
  - full cross-layer history export

## Test Coverage
Added tests:
- `tests/test_cross_layer_evaluation.py`
  - full report generation across providers
  - determinism and divergence signal validation
  - report/history export persistence
  - latest summary contract validation
- `tests/test_runtime_diagnostics_dashboard.py`
  - cross-layer diagnostics snapshot integration

## Architectural Notes
- No new runtime primitives were introduced.
- No orchestration/agent/distributed infrastructure was added.
- All logic is deterministic and replay-oriented.
- Cross-layer diagnostics are additive and optional.

## Optimization Philosophy in this Phase
Optimization recommendations are generated from measured signals only:
- semantic degradation
- replay nondeterminism
- cross-view over-divergence / over-redundancy
- projection overhead
- long-horizon erosion

This keeps optimization benchmark-driven and avoids heuristic drift.
