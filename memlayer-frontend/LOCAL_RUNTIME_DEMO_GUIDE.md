# MemLayer Local Runtime Demo Flow

Follow this deterministic sequence to demo the MemLayer kernel end-to-end locally.

## Step 1: Initialize System
1. Start the backend: `cd memlayer-backend && uvicorn app.main:app --reload --port 8000`
2. Start the frontend: `cd memlayer-frontend && npm run dev`
3. Navigate to `http://localhost:3000`

## Step 2: Seed Mock Runtime Data
1. Open the **Dashboard**.
2. Click the **Seed Runtime Data** button. This will trigger the backend `/console/seed-mock-data` endpoint to simulate real compilation, memory ingestion, and policy checks.

## Step 3: Verify the Kernel
Explore the subsystems in the following order to tell the MemLayer story:

1. **Workspaces**: See the newly created tenant environments.
2. **Compiler Viz**: View the adaptive assembly DAG and how memory was compressed.
3. **Coordination**: Examine the agent delegation topology and the 35%+ token savings achieved via shared cognition.
4. **View Engine**: See cached provider-shaped projections.
5. **Telemetry**: Verify the macro token-economics charts.
6. **Governance**: Inspect the exact immutable audit trail and semantic lineage graph of everything that just occurred.
