# Runtime Configuration Architecture — Deployment Profiles

## 1. Overview
The MemLayer Runtime Configuration System provides a unified, environment-aware mechanism for tuning the cognition substrate. It ensures that the runtime can adapt to different deployment topologies (Local, Hosted, Production) while maintaining deterministic behavior.

## 2. Configuration Hierarchy
Configuration is managed through `pydantic-settings`, allowing for:
1.  **Defaults**: Hardcoded safe defaults in `app/core/config.py`.
2.  **Environment Variables**: Overrides provided via the OS environment (highest priority).
3.  **Dotenv Files**: Local development overrides in `.env`.

## 3. Deployment Profiles

### 3.1. Local Profile (`storage_provider="local"`)
- **Database**: SQLite (`sqlite+aiosqlite`)
- **Redis**: Localhost or disabled (ephemeral memory)
- **Object Storage**: Local filesystem (`./.memlayer/storage`)
- **Goal**: Rapid developer iteration and offline testing.

### 3.2. Hosted/Production Profile (`storage_provider="s3"`)
- **Database**: PostgreSQL (`postgresql+asyncpg`)
- **Redis**: Dedicated cluster for coordination and locking.
- **Object Storage**: AWS S3 or MinIO for snapshots.
- **Goal**: High availability, multi-tenant isolation, and durable governance.

## 4. Subsystem Tuning

### 4.1. Persistence Config
- `async_database_url`: The primary entry point for the Async SQL kernel.
- `deterministic_mode`: When enabled, enforces strict sequence ordering even at the cost of slight latency.

### 4.2. Coordination Config
- `redis_host/port`: Connectivity for the distributed coordination layer.
- `distributed_locks`: Boolean to enable/disable lock-based workspace protection.

### 4.3. Telemetry & Replay Config
- `telemetry_flush_interval`: Frequency of background metric persistence.
- `replay_history_limit`: Maximum number of traces retained for the Operational Console.

## 5. Security & Tenant Scoping
The configuration system includes a global `app_current_tenant_id` (defaulting to "default"). In production, this is overridden dynamically per-request by middleware, but the configuration system provides the baseline defaults for tenant resource quotas (e.g., `top_k_memories`).

## 6. Implementation Example
```python
# app/core/config.py
class Settings(BaseSettings):
    database_url: str = "sqlite:///./memlayer.db"
    storage_provider: str = "local"
    # ...
```
To run in production:
`DATABASE_URL=postgresql+asyncpg://user:pass@host/db STORAGE_PROVIDER=s3 python main.py`
