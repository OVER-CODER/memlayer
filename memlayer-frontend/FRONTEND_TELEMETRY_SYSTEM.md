# Telemetry & Token Economics

The telemetry dashboard exposes the operational viability of the MemLayer kernel.

## Dashboard Components (`/app/telemetry`)
- **Token Efficiency Chart**: Recharts-based area chart visualizing raw `tokens_consumed` vs `tokens_saved`.
- **Latency Monitoring**: Tracks `coordination_duration_ms` per run.
- **Provider Benchmarks**: Aggregates token statistics per provider (e.g., Claude vs OpenAI), visualizing cost efficiency and routing outcomes.

Data is continuously polled every 5s from `/console/telemetry` via React Query to provide live ops capabilities.
