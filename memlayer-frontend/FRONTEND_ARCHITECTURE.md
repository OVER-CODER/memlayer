# MemLayer Frontend Architecture

The MemLayer Frontend is an operational console, NOT a consumer AI interface. It acts as the "glass" into the MemLayer cognition kernel.

## Core Stack
- **Framework**: Next.js 15 (App Router)
- **State Management**: Zustand (Client State), TanStack Query (Server State)
- **Styling**: Tailwind CSS
- **Visualization**: React Flow (Node DAGs), Recharts (Telemetry)
- **Icons**: Lucide React

## Design Principles
1. **Deterministic Rendering**: The UI is a strict function of the backend runtime state. No mock data or artificial states exist.
2. **High-Density Data**: Prioritizes raw telemetry, node graphs, and metrics over whitespace and consumer UI patterns.
3. **Replay-Awareness**: Every component is designed to render correctly whether the data is live telemetry or historical replay.

## Key Modules
1. **Workspace Kernel**: (`/app/workspaces`) Renders isolated tenant contexts and memory states.
2. **Compiler DAG**: (`/app/compiler`) Visualizes the step-by-step semantic reduction of context.
3. **Coordination Graph**: (`/app/coordination`) Renders the runtime topology of agent delegation and shared state.
4. **View Explorer**: (`/app/views`) Compares provider projections across the semantic bus.
5. **Governance Lineage**: (`/app/governance`) Explores immutable audit trails and semantic ancestry.
6. **Telemetry Dashboards**: (`/app/telemetry`) Realtime token economics and latency tracking.

## Determinism
All node ids, edge mappings, and charts map 1:1 with deterministic Backend identifiers (e.g., `checkpoint_id`, `derivation_id`, `report_id`).
