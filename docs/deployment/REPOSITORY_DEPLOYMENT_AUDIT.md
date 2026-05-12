# REPOSITORY DEPLOYMENT AUDIT

**Audit Date:** 2026-05-12  
**Branch:** `phase11/frontend-console`  
**Objective:** Prepare MemLayer backend for production-lite deployment to Render

---

## 1. RUNTIME ENTRYPOINTS

### Primary Entry Point
- **File:** `memlayer-backend/app/main.py`
- **Application:** FastAPI application
- **Port:** 8000 (default)
- **Command:** `uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Startup Sequence
1. Import FastAPI, CORS, routers
2. Call `init_db()` - synchronous table creation
3. Import security middleware
4. Create FastAPI app instance
5. Add middleware (tenant, auth, CORS)
6. Include routers (workspaces, chats, memories, console)
7. Define health endpoints (`/health`, `/api/config`)

### Alternative Entry Points
- Direct: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Debug: `python app/main.py` (when `DEBUG=true`)

---

## 2. STARTUP DEPENDENCY GRAPH

```
app/main.py
  ├── fastapi.FastAPI (core)
  ├── app.api.workspaces (router)
  ├── app.api.chats (router)
  ├── app.api.memories (router)
  ├── app.api.console (router)
  ├── app.db.session.init_db() [BLOCKING]
  │   └── app.db.models.Base.metadata.create_all()
  ├── app.security.middleware.tenant.TenantMiddleware
  └── app.security.middleware.authentication.AuthenticationMiddleware
```

**Critical Path:**
- `init_db()` must complete before middleware loads
- No async initialization in startup sequence
- All imports are synchronous

---

## 3. CURRENT DEPLOYMENT BLOCKERS

### BLOCKER 1: Hardcoded SQLite URLs
- `config.py` line 22-23: Default database URLs are SQLite
- `DATABASE_URL=sqlite:///./memlayer.db`
- `ASYNC_DATABASE_URL=sqlite+aiosqlite:///./memlayer.db`
- Need: PostgreSQL URLs for production

### BLOCKER 2: Local Filesystem Assumptions
- `config.py` line 33: `storage_local_path = "./.memlayer/storage"`
- Will fail on Render's ephemeral filesystem
- Need: External object storage (S3/MinIO) or disable snapshot feature

### BLOCKER 3: Redis Connection Without Retry
- `coordination_cache.py` line 26-32: Direct Redis connection
- No connection retry logic
- No graceful degradation if Redis unavailable

### BLOCKER 4: Missing Health Endpoints for External Services
- `/health` doesn't check DB connectivity
- `/health` doesn't check Redis connectivity
- Need: Deep health checks

### BLOCKER 5: Synchronous DB Initialization
- `main.py` line 12: `init_db()` runs synchronously at import time
- Will block startup if DB unavailable
- Need: Async initialization with retry

### BLOCKER 6: No Graceful Shutdown
- Application has no lifecycle event handlers
- No cleanup on SIGTERM/SIGINT

---

## 4. REQUIRED ENVIRONMENT VARIABLES

### Critical (Must Set)
```bash
# Database (PostgreSQL - Supabase)
DATABASE_URL=postgresql+asyncpg://[user]:[pass]@db.[project].supabase.co:6543/postgres
ASYNC_DATABASE_URL=postgresql+asyncpg://[user]:[pass]@db.[project].supabase.co:6543/postgres

# Redis (Upstash)
REDIS_HOST=[host].upstash.io
REDIS_PORT=6379
REDIS_PASSWORD=[password]

# Security
SECRET_KEY=[generate-strong-key]
SECURITY_ENABLED=true

# LLM Provider
GEMINI_API_KEY=[key]
```

### Important (Should Set)
```bash
# Server
DEBUG=false
LOG_LEVEL=INFO

# Runtime
DETERMINISTIC_MODE=true

# Object Storage (optional)
STORAGE_PROVIDER=local  # or s3/minio
```

### Optional (Can Default)
```bash
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384
TOP_K_MEMORIES=5
MEMORY_RETRIEVAL_THRESHOLD=0.3
```

---

## 5. REQUIRED EXTERNAL SERVICES

### PostgreSQL (Supabase)
- **Connection:** Requires asyncpg driver
- **Features Used:** pgvector (for embeddings), JSON columns
- **Connection Pool:** 20 connections + 10 overflow
- **URL Format:** `postgresql+asyncpg://user:pass@host:port/db`

### Redis (Upstash)
- **Connection:** Standard redis-py client
- **Features Used:** distributed locks, session cache, projection cache
- **Key Format:** `{tenant_id}:{prefix}:{key}` (tenant-isolated)
- **Timeout:** Default (no explicit timeout set)

### LLM Providers (Optional)
- **Gemini:** Primary provider
- **OpenAI:** Backup provider
- **Anthropic:** Backup provider

---

## 6. HEALTH ENDPOINTS

### Current Endpoints

| Endpoint | Method | Returns | Checks |
|----------|--------|---------|--------|
| `/health` | GET | `{"status": "healthy", "version": "0.1.0"}` | None (shallow) |
| `/api/config` | GET | Config object | None |

### Required Health Endpoints

| Endpoint | Method | Should Check |
|----------|--------|--------------|
| `/health` | GET | Basic liveness |
| `/health/ready` | GET | DB + Redis connectivity |
| `/metrics` | GET | Prometheus metrics |

---

## 7. MIGRATION FLOW

### Current Setup
- **Alembic Config:** `alembic.ini` exists
- **Migration Location:** `memlayer-backend/alembic/`
- **Script:** `alembic/env.py` (needs configuration)

### Current Issue
- `env.py` not configured with proper DATABASE_URL
- No migration scripts created yet
- `init_db()` uses `Base.metadata.create_all()` instead

### Required Migration Flow
```bash
# 1. Set DATABASE_URL to production PostgreSQL
export DATABASE_URL="postgresql+asyncpg://..."

# 2. Run Alembic migrations
alembic upgrade head

# 3. Verify tables created
psql -c "\dt"
```

---

## 8. PRODUCTION STARTUP SEQUENCE

### Ideal Production Startup

1. **Load Environment Variables**
   - Validate required vars present
   - Set defaults for optional vars

2. **Initialize Logging**
   - Set structured JSON format
   - Configure log levels

3. **Connect to Database**
   - Async connection with retry (5 attempts, 2s backoff)
   - Run Alembic migrations
   - Verify connection with health check

4. **Connect to Redis**
   - Connect with retry (3 attempts, 1s backoff)
   - If fails: log warning, continue degraded (no locks/caching)

5. **Initialize Runtime**
   - Load security middleware
   - Register routers

6. **Start Server**
   - Bind to `0.0.0.0:$PORT`
   - Emit "Server ready" log

7. **Begin Health Monitoring**
   - Periodic DB ping
   - Periodic Redis ping

---

## 9. RUNTIME ASSUMPTIONS INCOMPATIBLE WITH RENDER

### Assumption 1: Local Persistent Storage
- **Problem:** `storage_local_path = "./.memlayer/storage"`
- **Impact:** Files written to ephemeral filesystem
- **Fix:** Use external S3/MinIO or disable snapshots

### Assumption 2: SQLite Fallback
- **Problem:** Default DATABASE_URL is SQLite
- **Impact:** Works locally, fails in container
- **Fix:** Require PostgreSQL URL in production

### Assumption 3: Always-On Redis
- **Problem:** No graceful degradation
- **Impact:** Runtime crash if Redis unavailable
- **Fix:** Implement try/catch around Redis operations

### Assumption 4: Debug Mode Available
- **Problem:** `debug=True` loads debug tooling
- **Impact:** Exposes internals in production
- **Fix:** Ensure `DEBUG=false` in production

---

## 10. SQLITE REMNANTS PRESENT

### Found SQLite References

| File | Line | Setting | Default |
|------|------|---------|---------|
| `app/core/config.py` | 22 | `database_url` | `sqlite:///./memlayer.db` |
| `app/core/config.py` | 23 | `async_database_url` | `sqlite+aiosqlite:///./memlayer.db` |
| `app/db/session.py` | 13 | sync engine | Uses `settings.database_url` |
| `app/db/session.py` | 21 | async engine | Uses `settings.async_database_url` |

**Action Required:** Ensure DATABASE_URL is always PostgreSQL in production

---

## 11. LOCAL FILESYSTEM ASSUMPTIONS

### Found Filesystem Dependencies

| File | Line | Usage | Risk |
|------|------|-------|------|
| `app/core/config.py` | 33 | `storage_local_path` | HIGH - won't persist on Render |
| `app/db/session.py` | 59 | `Base.metadata.create_all()` | LOW - creates tables, no data |
| N/A | N/A | SQLite database file | HIGH - won't persist |

**Action Required:** 
- Use Supabase for all persistent data
- Disable or externalize object storage

---

## 12. STARTUP RACE-CONDITION RISKS

### Identified Risks

| Risk | Description | Severity |
|------|-------------|----------|
| Import-time DB init | `init_db()` called at import time, not async | MEDIUM |
| Middleware dependency | TenantMiddleware may expect DB ready | MEDIUM |
| Circular imports | Security modules may import runtime modules | LOW |

### Recommended Fix
```python
# Replace sync init_db with async lifecycle
@app.on_event("startup")
async def startup():
    await verify_db_connection()
    await run_migrations()
```

---

## 13. ASYNC BOOT RISKS

### Current Implementation Issues
1. **Sync DB Init:** `init_db()` is synchronous, called at import time
2. **No Startup Event:** No FastAPI lifespan/startup event handler
3. **Blocking Middleware:** Security middleware may not be async-safe

### Recommended Fix
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_async_db()
    yield
    # Shutdown
    await cleanup()

app = FastAPI(lifespan=lifespan)
```

---

## 14. TELEMETRY RISKS

### Prometheus Integration Status
- ✅ Prometheus client library imported (`app/core/observability.py`)
- ✅ Metrics defined: tokens_saved, compilation_latency, active_coordinations, etc.
- ❌ No `/metrics` endpoint exposed in main.py

### Action Required
- Add `/metrics` endpoint using `prometheus_client` `generate_latest()`

---

## 15. REPLAY/GOVERNANCE PRODUCTION RISKS

### Replay System
- ✅ Replay engine exists in `app/runtime/replay_engine.py`
- ✅ Deterministic mode configured (`DETERMINISTIC_MODE=true`)
- ⚠️  No production validation of replay on PostgreSQL

### Governance System
- ✅ Governance modules exist in `app/governance/`
- ✅ Audit trail, lineage, policy engine implemented
- ⚠️  Audit trail append-only semantics need verification on PostgreSQL

### Recommended Validation
1. Create replay trace on production
2. Verify trace can be retrieved from PostgreSQL
3. Verify governance audit records persist correctly

---

## DEPLOYMENT READINESS SUMMARY

### ✅ Ready Components
- FastAPI application structure
- Security middleware
- API routers (workspaces, chats, memories, console)
- Observability infrastructure (Prometheus metrics)
- Dockerfile exists

### 🔴 Deployment Blockers
1. SQLite URLs as defaults (must override)
2. Local filesystem storage (must disable/externalize)
3. No deep health checks
4. No async startup lifecycle
5. No graceful degradation for Redis
6. No migration automation
7. No `/metrics` endpoint

### 🟡 Risk Items
- Import-time DB initialization
- No graceful shutdown
- Untested PostgreSQL compatibility
- Untested Upstash Redis compatibility

---

## RECOMMENDED ACTIONS (Priority Order)

1. **CRITICAL:** Add `/metrics` endpoint
2. **CRITICAL:** Add `/health/ready` deep health check
3. **CRITICAL:** Add async startup lifecycle with DB/Redis verification
4. **HIGH:** Add Redis graceful degradation
5. **HIGH:** Configure Alembic for production PostgreSQL
6. **HIGH:** Disable or externalize local storage
7. **MEDIUM:** Add graceful shutdown handlers
8. **MEDIUM:** Validate replay trace persistence
9. **MEDIUM:** Validate governance audit persistence