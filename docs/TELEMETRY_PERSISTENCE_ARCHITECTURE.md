# Telemetry Persistence Architecture — High-Fidelity Observability

## 1. Overview
The Telemetry Persistence layer transitions from in-memory buffers to a partitioned, replay-linked storage system. It provides the "Runtime Context" for every cognition event, enabling deep performance analysis and economic auditing.

## 2. Event-Trace Relationship
Telemetry is strictly hierarchical:
1.  **Replay Trace**: The parent container for an entire cognition run.
2.  **Telemetry Events**: Individual stage records (Ranking, Assembly, etc.) linked to the `trace_id`.
3.  **Metrics**: Granular data points (tokens, ms, scores) embedded in the event `JSONB`.

## 3. Storage Strategy

### 3.1. Append-Safe Persistence
Telemetry events are written using `INSERT`-only semantics. To minimize impact on runtime latency, telemetry writes are:
- **Buffered**: Stage records are accumulated in an async buffer during execution.
- **Batched**: Flushed to the database in a single transaction after the execution finishes (or at predefined intervals).

### 3.2. Partitioning
In production (PostgreSQL), `telemetry_events` will be partitioned by `timestamp`.
- **Active Partition**: Current day/week. Optimized for high-frequency writes.
- **Historical Partition**: Read-optimized for dashboards and long-term trend analysis.

## 4. Replay-Linked Retrieval
Telemetry is useless without context. Every telemetry dashboard in the Operational Console allows "Drill-Down":
- Clicking a latency spike → Loads the corresponding `ReplayTrace`.
- Inspecting a Replay Trace → Visualizes the associated `TelemetryEvents` in the stage breakdown.

## 5. Economic Persistence (Token Analytics)
Token usage is persisted at the stage level:
- `raw_tokens_in`
- `compiled_tokens_out`
- `savings_ratio`
This allows for "Semantic ROI" calculations: measuring the value added by each compilation stage vs. its token cost.

## 6. Implementation Roadmap
- [x] Define `TelemetryEvent` SQLAlchemy Model.
- [ ] Implement `AsyncTelemetryBuffer` for non-blocking writes.
- [ ] Add `TraceID` headers to all telemetry ingestion APIs.
- [ ] Implement `MetricAggregator` for partitioned time-series queries.
