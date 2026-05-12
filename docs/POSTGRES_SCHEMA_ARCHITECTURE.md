# PostgreSQL Schema Architecture — Cognition-Native Storage

## 1. Overview
The MemLayer PostgreSQL schema is designed for **deterministic cognition storage**. It utilizes `pgvector` for semantic search, `JSONB` for flexible but deterministic traces, and strict partitioning for telemetry and audit trails.

## 2. Core Extension Requirements
- `pgvector`: For embedding storage and similarity search.
- `uuid-ossp`: For primary key generation.
- `pgcrypto`: For integrity hash verification.

## 3. Database Schema Design

### 3.1. Workspaces Table
Stores mutable metadata for cognition environments.
```sql
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(128) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    default_provider VARCHAR(50) DEFAULT 'claude',
    token_budget INTEGER DEFAULT 4000,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_workspaces_tenant ON workspaces(tenant_id);
```

### 3.2. Memories Table
Stores semantic units with vector embeddings.
```sql
CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    tenant_id VARCHAR(128) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    raw_content TEXT NOT NULL,
    summary TEXT,
    embedding VECTOR(384), -- Dimension matches sentence-transformers
    importance_score FLOAT DEFAULT 0.5,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_memories_workspace_tenant ON memories(workspace_id, tenant_id);
CREATE INDEX idx_memories_vector ON memories USING hnsw (embedding vector_cosine_ops);
```

### 3.3. Replay Traces Table
Immutable record of runtime executions.
```sql
CREATE TABLE replay_traces (
    trace_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    tenant_id VARCHAR(128) NOT NULL,
    query TEXT NOT NULL,
    execution_plan JSONB NOT NULL, -- Canonical JSON
    trace_data JSONB NOT NULL,     -- Full stage metrics
    integrity_hash VARCHAR(64) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_replay_traces_workspace ON replay_traces(workspace_id, timestamp DESC);
```

### 3.4. Semantic Lineage Table
Recursive ancestry tracking for cognition state.
```sql
CREATE TABLE semantic_lineage (
    checkpoint_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    tenant_id VARCHAR(128) NOT NULL,
    state_hash VARCHAR(64) NOT NULL,
    parent_id UUID REFERENCES semantic_lineage(checkpoint_id),
    operation_id VARCHAR(128) NOT NULL,
    metadata JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_lineage_ancestry ON semantic_lineage(workspace_id, parent_id);
```

### 3.5. Governance Audit Table
Append-only trust trail.
```sql
CREATE TABLE governance_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    tenant_id VARCHAR(128) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB NOT NULL,
    integrity_hash VARCHAR(64) NOT NULL,
    recorded_by VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_timeline ON governance_audit(workspace_id, timestamp DESC);
```

### 3.6. Telemetry Events Table
Time-series metrics storage.
```sql
CREATE TABLE telemetry_events (
    id BIGSERIAL PRIMARY KEY,
    trace_id UUID REFERENCES replay_traces(trace_id),
    tenant_id VARCHAR(128) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    duration_ms FLOAT,
    token_metrics JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
-- Optional: Partition by range (timestamp)
CREATE INDEX idx_telemetry_trace ON telemetry_events(trace_id);
```

## 4. Replay Traversal Optimization
To optimize for historical replay reconstruction, the `replay_traces` and `semantic_lineage` tables use composite indexes on `(workspace_id, timestamp DESC)`. This allows the Replay Engine to rapidly pull the exact sequence of events leading to a specific state.

## 5. Tenant Isolation
Every query MUST include a `WHERE tenant_id = :tenant_id` clause. PostgreSQL **Row-Level Security (RLS)** will be enabled for all tables to provide a kernel-level guarantee of data isolation.

```sql
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_policy ON workspaces 
USING (tenant_id = current_setting('app.current_tenant_id'));
```
