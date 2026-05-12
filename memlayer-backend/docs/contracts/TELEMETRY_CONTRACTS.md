# Telemetry & Observability Contracts — v1

## 1. Overview
Defines the metrics and tracing guarantees for operational visibility.

## 2. Metric Stability
- **Counter**: `memlayer_tokens_saved_total`
- **Histogram**: `memlayer_compilation_duration_seconds`
- **Gauge**: `memlayer_active_coordinations`
- **Summary**: `memlayer_replay_fidelity_score`
- **Constraint**: Metric names and label sets (e.g., `workspace_id`, `provider`) MUST NOT be changed without a minor version increment.

## 3. Trace Correlation
- **Contract**: Every runtime event MUST carry the parent `trace_id`.
- **OTEL Integration**: Spans MUST follow the OpenTelemetry semantic conventions for Database and HTTP.

## 4. Secret Redaction
- **Contract**: `SecretManager.redact_dict()` MUST be applied to all telemetry payloads before persistence or export.
- **Forbidden**: Storing raw API keys, tokens, or passwords in Prometheus labels or OTEL tags.

## 5. Event Latency
- **Guarantee**: Telemetry recording MUST NOT add more than 5ms of overhead to the hot cognition path.
- **Mitigation**: Async buffering and batching for high-volume telemetry streams.

## 6. Retention
- **Policy**: Telemetry events in SQL are considered "Hot Logs" (30-day retention recommended).
- **Archival**: Aggregated metrics are preserved in Prometheus/Grafana.
