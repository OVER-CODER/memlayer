# Operational Observability — Runtime Visibility

## 1. Overview
Operational Observability provides high-fidelity visibility into the MemLayer cognition substrate. It tracks token economics, compilation latency, replay fidelity, and governance health in real-time.

## 2. Metrics Stack (Prometheus)

### 2.1. Token Economics
- `memlayer_tokens_saved_total`: Cumulative tokens saved via deduplication and compression.
- **Goal**: Measure the "Semantic ROI" of the assembly pipeline.

### 2.2. Compilation Latency
- `memlayer_compilation_duration_seconds`: Histogram of time spent in each pipeline stage (Ranking, Assembly, etc.).
- **Goal**: Identify performance bottlenecks and provider-induced latency spikes.

### 2.3. Replay Fidelity
- `memlayer_replay_fidelity_score`: Summary of how well historical replays match original executions.
- **Goal**: Maintain the "Determinism Invariant" (target score = 1.0).

### 2.4. Governance Monitoring
- `memlayer_governance_violations_total`: Count of policy violations (e.g., unauthorized access, context leakage).

## 3. Distributed Tracing (OpenTelemetry)
MemLayer utilizes OpenTelemetry (OTEL) for cross-subsystem trace propagation.
- **Correlation IDs**: Every request is assigned a `trace_id` that links API calls, database transactions, Redis locks, and agent execution logs.
- **Replay Linkage**: The OTEL `trace_id` is persisted in the `replay_traces` table, allowing operators to move from a Prometheus spike directly to a bit-for-bit replay in the Console.

## 4. Structured Logging
Logs are emitted in structured JSON format to support high-speed ingestion and searching in ELK/Grafana Loki.
- **Pattern**: `{"timestamp": "...", "level": "INFO", "trace_id": "...", "event": "...", "data": {...}}`

## 5. Health Probes
- `/health`: Liveness probe for Docker/K8s. Returns basic kernel status.
- `/health/ready`: Readiness probe. Verifies connectivity to PostgreSQL, Redis, and Object Storage.
- `/health/diagnostics`: Deep check of governance integrity and replay engine status.

## 6. Implementation Checklist
- [x] Implement `RuntimeObservability` service with Prometheus counters/histograms.
- [x] Integrate OTEL instrumentation.
- [x] Add structured JSON logging.
- [x] Implement `/health` endpoints in `app/main.py`.
