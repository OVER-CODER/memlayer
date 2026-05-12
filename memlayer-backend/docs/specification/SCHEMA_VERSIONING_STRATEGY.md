# Schema Versioning Strategy — v1

## 1. Overview
Ensures that the MemLayer persistence layer can evolve without breaking historical determinism or replay integrity.

## 2. Evolution Rules

### 2.1. Replay-Safe Migrations
The following changes are considered **Replay-Safe**:
- Adding new optional columns.
- Increasing column length (e.g., `VARCHAR(100)` -> `VARCHAR(255)`).
- Adding new non-unique indexes.
- Adding entirely new tables.

### 2.2. Replay-Breaking Migrations (Prohibited in v1)
The following changes are **Prohibited** as they break historical execution integrity:
- Renaming or deleting columns used in `ReplayTrace` serialization.
- Changing data types of existing columns.
- Modifying the `integrity_hash` calculation algorithm.
- Deleting historical audit or lineage rows.

## 3. Migration Lifecycle (Alembic)
1. **Develop**: Create migration script in `alembic/versions`.
2. **Validate**: Run `pytest tests/specification/test_replay_compatibility.py`.
3. **Audit**: Document the migration impact in `MIGRATION_AUDIT_LOG.md`.
4. **Deploy**: Apply to production using `alembic upgrade head`.

## 4. Replay-Safe Schema Check
Before any migration is finalized, the `RuntimeValidator` MUST confirm that:
- Existing traces can still be deserialized.
- The `CanonicalSerializer` output remains identical for a reference memory set.

## 5. Prohibited Changes
- **NO** mutation of `governance_audit` timestamps.
- **NO** modification of lineage `parent_id` links.
- **NO** removal of `tenant_id` constraints.

## 6. Versioning Window
MemLayer v1 supports schema versions that maintain backward compatibility with traces created since the start of Phase B. Breaking changes require a migration to MemLayer v2.
