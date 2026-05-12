# Frontend Replay System

MemLayer is deterministic and replayable. The frontend is built to respect this capability natively.

## The Replay Console (`/app/replay`)
The Replay Console visualizes `coordination_traces` dynamically.
- Traces expose exact token savings, coordination latency, provider routing, and reuse ratios.
- Time travel operates linearly along `report_id` vectors.

## Replay Integrity
The frontend does not simulate replay state. It fetches historical `reports` and `snapshots` exactly as they were recorded by the backend.
- **Visualizer**: Rendered as a timeline sequence showing explicit metrics per node execution.
- **State Diffs**: Not currently rendered interactively, but accessible via deterministic checksum matching in the View Engine Explorer.
