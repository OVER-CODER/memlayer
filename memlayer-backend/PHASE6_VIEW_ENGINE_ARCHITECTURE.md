# Phase 6 — View Engine Compiler Architecture

## Objective
Phase 6 introduces cognition virtualization: deterministic, replayable, provider-aware semantic projections compiled from the same shared workspace cognition state.

The View Engine is not prompt templating and not orchestration. It is a semantic projection compiler layer between shared runtime cognition and future runtime consumers.

## Implemented Components

### 1. View Definition Framework
File: `app/view_engine/definitions.py`

- Provides canonical view contracts for:
  - `research`
  - `drafter`
  - `tool_agent`
  - `critic`
- Encodes:
  - semantic objectives
  - optimization priorities
  - token distribution preferences
  - compression preference
  - provider-specific shaping profiles (`claude`, `openai`, `gemini`)

### 2. View Engine Compiler
File: `app/view_engine/compiler.py`

- Compiles role-specific views from `WorkspaceSemanticState`.
- Integrates directly with `IntegratedRuntimeSystem` and adaptive assembly pipeline.
- Performs deterministic:
  - memory ranking/selection
  - token budget resolution
  - provider-aware query shaping
- Emits:
  - compiled runtime trace
  - semantic projection
  - quality report
  - view compilation metrics

### 3. Semantic Projection Engine
File: `app/view_engine/projection.py`

- Projects compiled context into view-specific structure.
- Tracks:
  - projection checksum
  - section-level overlap
  - cross-view divergence/overlap
- Supports projection set comparison for diagnostics and benchmarks.

### 4. View Quality Evaluator
File: `app/view_engine/quality.py`

- Scores projections on:
  - semantic preservation
  - reasoning continuity
  - specialization effectiveness
  - token efficiency
  - projection fidelity
  - provider compatibility
- Produces comparable quality reports across view/provider variants.

### 5. View Replay Engine
File: `app/view_engine/replay.py`

- Records replay traces for view outputs.
- Replays from identical semantic state and validates deterministic checksum stability.
- Supports replay comparison and replay statistics export.

### 6. View Diagnostics Dashboard
File: `app/view_engine/diagnostics.py`

- Generates developer diagnostics snapshots:
  - view distribution
  - provider distribution
  - quality summary
  - projection comparison report
  - replay determinism summary
- Exports JSON snapshots and profiler-style console reports.

## Runtime Observability Integration

### Runtime Dashboard Bridge
File: `app/runtime/diagnostics_dashboard.py`

Runtime diagnostics snapshots now include optional embedded view diagnostics under `view_engine_diagnostics` when a view dashboard is attached.

Added:
- `view_engine_diagnostics` in runtime snapshot serialization
- automatic capture of view snapshot data
- aggregated view metrics (`total_views_compiled`, `avg_view_quality`)

This preserves existing Phase 5B diagnostics behavior while enabling unified Phase 6 observability.

## Determinism and Replayability

Determinism safeguards:
- stable checksum of semantic state (`WorkspaceSemanticState.state_checksum()`)
- deterministic memory scoring and ordering
- deterministic projection checksums
- replay grouping by workspace/view/provider/state-checksum

Replay artifacts and diagnostics are exportable JSON for historical comparison workflows.

## Benchmarking

Benchmark runner:
- `benchmarks/phase6_view_engine/run_view_engine_benchmarks.py`

Coverage:
- multi-provider (`claude`, `openai`, `gemini`)
- multi-workload (`research`, `drafting`, `tooling`, `critique`)
- all four foundational views
- replay determinism checks
- diagnostics snapshot generation

Output:
- row-level benchmark records
- summary report
- diagnostics console output

## Validation Status

Current validation confirms:
- full test suite remains green
- view compilation deterministic under repeated replay
- cross-view divergence is measurable and stable
- diagnostics snapshots are exportable and replay-compatible
- provider-aware shaping produces differentiated view budgets/projections

## Non-Goals Preserved

This implementation explicitly avoids:
- agent loops
- orchestration systems
- distributed runtime architecture
- workflow automation layers
- new autonomous primitives

The Phase 6 layer remains a compiler/runtime projection subsystem aligned with MemLayer core architecture.
