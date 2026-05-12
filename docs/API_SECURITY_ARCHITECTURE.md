# API Security Architecture — Edge Protection

## 1. Overview
The API Security layer provides the first line of defense for the MemLayer runtime. It enforces authentication, tenant propagation, and request integrity before any cognition logic is executed.

## 2. Middleware Chain
The FastAPI application uses a layered middleware architecture (bottom-to-top execution):

1.  **CORSMiddleware**: Manages cross-origin resource sharing for the Operational Console.
2.  **AuthenticationMiddleware**: Resolves `AuthContext` from JWT or API Key headers.
3.  **TenantMiddleware**: Propagates `tenant_id` into a thread-local/task-local `ContextVar` for service-level isolation.
4.  **AuditMiddleware**: (Integrated into Governance) Records the request footprint for the audit trail.

## 3. Request Identity Propagation
To ensure determinism and traceability:
- Every request is assigned a `trace_id` (either provided by the caller or generated).
- This `trace_id` is propagated through all async tasks and persisted with every memory, checkpoint, and audit event.
- The `subject_id` (authenticated user) is linked to every state-changing operation.

## 4. Tenant Isolation Enforcement
Isolation is enforced at multiple layers:
- **Middleware**: Blocks any request where the target `tenant_id` does not match the token's `tenant_id`.
- **Repository**: Every query includes an implicit `filter(tenant_id == current_tenant())` using the propagated context.
- **Redis**: Keys are prefixed with the tenant ID to prevent cross-tenant cache or lock contamination.

## 5. Security Event Mapping

| Event | Result | Audit Action |
| :--- | :--- | :--- |
| **Valid JWT** | 200 OK | `AUTH_GRANTED` |
| **Invalid Token** | 401 Unauthorized | `AUTH_FAILURE` (Security Alert) |
| **Cross-Tenant Access**| 403 Forbidden | `TENANT_VIOLATION` (High Severity) |
| **Rate Limit Exceeded**| 429 Too Many Requests | `RATE_LIMIT_EVENT` |

## 6. Implementation Status
- [x] JWT / API Key support.
- [x] ContextVar tenant propagation.
- [x] Zero-leakage middleware.
- [ ] Rate limiting (Reserved for Phase D).
- [ ] Row-Level Security (Postgres Only).

## 7. Conclusion
The API Security Architecture ensures that the MemLayer runtime is both open to authorized agents and completely impenetrable to unauthorized actors, maintaining the "Cognition Trust Boundary" at the edge.
