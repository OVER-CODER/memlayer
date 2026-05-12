# Governance Layer Contracts — v1

## 1. Overview
Defines the trust and auditability guarantees for the MemLayer runtime.

## 2. Audit Immutability
- **Contract**: `GovernanceAudit` table is append-only.
- **Enforcement**: Middleware and Repository layers reject any `UPDATE` or `DELETE` requests on audit rows.
- **Verification**: Periodic hash-chain verification of the audit trail.

## 3. Identity Linking
- **Requirement**: Every governance event MUST be linked to a `subject_id` (Auth Identity).
- **Lineage Correlation**: Checkpoints MUST link to the `TraceID` that generated them.

## 4. Policy Enforcement
- **Contract**: Policy checks occur BEFORE the compilation stage.
- **Result**: Violation triggers an immediate `403 Forbidden` and records an `AUTH_VIOLATION` event.

## 5. Traceability Guarantee
- **Invariant**: Any memory existing in the workspace MUST be traceable to a specific `TraceID` and `AuditEntry`.
- **Constraint**: Deleting a workspace is the ONLY way to remove governance artifacts (Terminal Operation).

## 6. Verification Semantics
- `verify_lineage(workspace_id)`: Recursively validates the hash chain from current leaf to root.
- `verify_trace(trace_id)`: Validates the trace's `integrity_hash` against re-serialized plan.
