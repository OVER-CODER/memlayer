# Frontend Runtime Integration

The MemLayer Frontend connects exclusively to `app.api.console.py`, which securely bridges the Next.js frontend to the core runtime SDKs.

## API Contracts (`lib/api.ts`)
- **Transport**: Standard HTTP via Axios, exposed through `/api/console/*`.
- **Typing**: Responses are typed in TS mirroring the Python Dataclass structures.
- **Server State**: Managed strictly through TanStack Query to ensure query caching, deduplication, and automatic refetching on telemetry ticks.

## Core Endpoints
- `GET /console/workspaces` -> Lists tenant-isolated workspaces.
- `GET /console/telemetry` -> Returns high-level latency, savings, and token economics.
- `GET /console/compiler/pipeline` -> Retrieves adaptive assembly DAG metrics.
- `GET /console/telemetry/coordination-traces` -> Fetches recent semantic delegations.
- `GET /console/governance/lineage` -> Exposes semantic state tracking and lineage derivations.

No backend objects are imported. The bridge guarantees isolation between Python runtime execution and React hydration loops.
