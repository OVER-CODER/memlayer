# Phase D1.5 - Production Validation Framework

## Overview

This framework validates that the deployed MemLayer production runtime preserves core architectural invariants under real-world operational pressure.

## Test Files Created

```
tests/production/
├── production_runner.py       # Main orchestrator
├── helpers.py                 # Authentication & API helpers
├── test_concurrent_ingestion.py       # Redis lock correctness, no deadlocks
├── test_longitudinal_growth.py        # Lineage depth traversal
├── test_replay_integrity.py           # Replay determinism (1.0 fidelity)
├── test_governance_integrity.py       # Audit trails, lineage immutability
├── test_snapshot_recovery.py          # Object storage snapshots
├── test_redis_coordination.py        # Distributed locking
├── test_connection_resilience.py     # Connection drop recovery
├── test_partial_failure_recovery.py  # Transaction atomicity
├── test_telemetry_pipeline.py        # OTEL trace propagation
├── test_cold_restart_recovery.py     # State restoration
├── test_async_ordering.py            # Monotonic sequence IDs
├── test_pgvector_scaling.py          # Vector retrieval scaling
├── test_high_volume_replay.py        # High volume trace replay
└── test_tenant_isolation.py          # Zero cross-tenant leakage
```

## Running Tests

```bash
cd memlayer-backend
python -m tests.production.production_runner
```

Or run individual tests:

```bash
python -m tests.production.test_replay_integrity
```

## Production Status

- **URL**: https://memlayer-prod.onrender.com
- **Database**: Neon PostgreSQL ✓ Connected
- **Redis**: Upstash ✓ Connected

## Test Authentication

The tests use JWT authentication with:
- Token generated using production secret key
- Tenant ID: test-tenant
- Role: admin

## Key Validation Targets

1. **Replay Determinism**: Fidelity must equal 1.0
2. **Tenant Isolation**: Zero cross-tenant leakage
3. **Governance**: Append-only audit trails
4. **Async Ordering**: Monotonic sequence IDs
5. **Failure Recovery**: No orphan lineage

## Known Issues

- Tests need to be updated to consistently use authentication headers
- Some API endpoints may need adjustment based on actual implementation

## Next Steps

1. Run individual tests to verify functionality
2. Fix any test failures
3. Generate validation reports in `docs/production_validation/`
4. Review remaining operational risks