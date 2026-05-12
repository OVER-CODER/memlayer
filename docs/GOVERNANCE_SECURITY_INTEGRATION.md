# Governance Security Integration — Immutable Identity Lineage

## 1. Overview
The Governance layer has been extended to capture security-critical identity and authorization events. This creates an immutable link between "Who performed the action" and "What semantic state was created."

## 2. Security Event Schema

New event types added to `GovernanceAudit.event_type`:
- `AUTH_LOGIN_SUCCESS`: Recording of a successful identity verification.
- `AUTH_DENIED`: Unauthorized attempt to access a resource.
- `RBAC_VIOLATION`: Authorized user attempting an unauthorized permission.
- `TENANT_LEAK_PREVENTED`: Middleware blocking a cross-tenant access attempt.
- `INTEGRITY_VIOLATION`: Checksum mismatch detected during re-hydration.

## 3. Identity-Bound Lineage
Every `SemanticLineage` checkpoint now includes the `subject_id` (User/Agent) of the creator in its metadata.
- **Traceability**: Given any state in the past, the system can definitively identify the authenticated subject responsible for that specific cognition turn.
- **Verification**: The `integrity_hash` of the lineage record now includes the `subject_id`, ensuring that identity cannot be retroactively tampered with without breaking the hash chain.

## 4. Replay Authorization Tracking
Replay execution is itself a governed event:
- Every time a `ReplayTrace` is re-hydrated, a `REPLAY_ACCESS` event is logged in the audit trail.
- This event includes the `subject_id` of the auditor and the `trace_id` being accessed.

## 5. Security Compliance Export
The `GovernanceAudit` trail can be exported as a "Security Proof" archive:
- **Format**: Signed JSON manifest with SHA256 checksums.
- **Usage**: Provides verifiable evidence for legal discovery or organizational compliance reviews.

## 6. Implementation Checklist
- [x] Integrate `AuthContext` into `GovernanceAudit` logging.
- [x] Implement high-severity alerting for `AUTH_DENIED` events.
- [x] Ensure `subject_id` is part of the `SemanticLineage` integrity chain.
- [x] Redact sensitive auth metadata (tokens/keys) from exported audit trails.

## 7. Conclusion
Security is no longer a wrapper; it is an **Architectural Invariant** of the MemLayer governance substrate. The identity of every agent is permanently woven into the semantic fabric of the runtime.
