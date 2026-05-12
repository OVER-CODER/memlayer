# RBAC Architecture — Secure Cognition Governance

## 1. Overview
The MemLayer RBAC system provides a deterministic, role-bound authorization framework designed specifically for the cognition runtime. It ensures that access to sensitive artifacts (lineage, replay, snapshots) is restricted based on clear organizational roles.

## 2. Role Taxonomy

| Role | Target Persona | Scope |
| :--- | :--- | :--- |
| **platform_admin** | Global Infrastructure Admin | All Tenants / All Permissions |
| **tenant_admin** | Enterprise Organization Admin | Single Tenant / All Workspace Ops |
| **operator** | Runtime Support / SRE | Single Tenant / Monitoring & Audit |
| **developer** | Agent Developer / Engineer | Single Tenant / Read-Write Ops |
| **viewer** | Business Analyst / Stakeholder | Single Tenant / Read-Only Governance |
| **replay_auditor** | Legal / Compliance Auditor | Single Tenant / Replay & Audit Only |

## 3. Permission Model
Permissions are granular and resource-oriented:
- `workspace:read/write`: Core lifecycle operations.
- `replay:access`: Ability to re-hydrate and view historical execution traces.
- `governance:access`: Ability to view the immutable audit trail and policies.
- `lineage:access`: Ability to traverse the semantic ancestry DAG.
- `coordination:control`: Ability to manage Redis locks and shared state.

## 4. Deterministic Evaluation
Authorization is evaluated using the following logic:
1.  **Identity Resolution**: Extract `role` from the verified JWT or API Key.
2.  **Permission Mapping**: Lookup the static `ROLE_PERMISSIONS` set.
3.  **Tenant Bound**: Verify that `auth.tenant_id` matches the `target_resource.tenant_id`.
4.  **Admin Bypass**: The `platform_admin` role bypasses all tenant-level checks for cross-tenant infrastructure maintenance.

## 5. Audit Integration
Every authorization decision is recorded in the `GovernanceAudit` trail:
- **Success**: Logged as an `AUTH_GRANTED` event.
- **Failure**: Logged as an `AUTH_DENIED` event with high severity, triggering an immediate telemetry alert.

## 6. Implementation Example
```python
from app.security.authorization import AuthorizationEngine
from app.security.rbac import Permission

# Inside a FastAPI endpoint
AuthorizationEngine.check_permission(auth, Permission.REPLAY_ACCESS)
AuthorizationEngine.verify_tenant_access(auth, target_workspace.tenant_id)
```
