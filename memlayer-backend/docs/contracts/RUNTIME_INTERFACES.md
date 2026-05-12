# Runtime Internal Interface Contracts — v1

## 1. Overview
Defines the immutable internal contracts between the core cognition substrate components.

## 2. Adaptive Assembly Pipeline
- **Interface**: `IAssemblyPipeline`
- **Immutable Expectation**: Must return a `CompilationResult` with stable memory ordering.
- **Forbidden**: Non-deterministic ranking models in production mode.

## 3. View Engine
- **Interface**: `IViewCompiler`
- **Immutable Expectation**: Compiling the same memory set + query MUST yield identical text projections.
- **Extension Point**: Custom `Template` providers are allowed if they follow the `DeterministicTemplate` base.

## 4. Replay Engine
- **Interface**: `IReplayEngine`
- **Guarantee**: `reconstruct(trace_id)` must re-hydrate the EXACT state at the time of trace creation.
- **Constraint**: Trace data must be serialized via `CanonicalSerializer`.

## 5. Coordination Layer
- **Interface**: `ICoordinationLayer`
- **Guarantee**: Lock acquisition is tenant-isolated.
- **Concurrency Assumption**: Single-writer per workspace via distributed locks.

## 6. Serialization Contract
- **Component**: `CanonicalSerializer`
- **Contract**: `hash(data) == hash(data_prime)` IF `data` and `data_prime` are semantically identical.
- **Rule**: Keys MUST be sorted alphabetically. Whitespace MUST be minified.

## 7. Async Guarantees
- All internal runtime methods MUST be `async`.
- `ContextVar` propagation MUST be preserved across task boundaries.
- Database sessions MUST NOT be shared across concurrent cognitive turns.
