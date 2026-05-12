# Security & Authentication Contracts — v1

## 1. Overview
Defines the trust and isolation guarantees for enterprise runtime security.

## 2. Authentication
- **Contract**: `AuthContext` is the immutable source of truth for every request.
- **Payload**: MUST contain `subject`, `tenant_id`, and `role`.
- **Validation**: JWTs MUST be signed with the system `secret_key` using `HS256`.

## 3. RBAC Enforcement
- **Constraint**: Authorization checks MUST happen at the service entry point.
- **Rule**: Permissions are additive. `PlatformAdmin` has universal access.
- **Forbidden**: Hardcoded "User" IDs in business logic. Always use `AuthContext.subject`.

## 4. Tenant Isolation
- **API**: Blocked by `AuthenticationMiddleware`.
- **Persistence**: Blocked by `TenantMiddleware` and `get_current_tenant()`.
- **Redis**: Blocked by key-prefixing.
- **Object Storage**: Blocked by path-prefixing.

## 5. Secret Protection
- **Contract**: API keys for LLM providers are stored as encrypted environment secrets.
- **Telemetry**: Redaction patterns are applied to all output streams.
- **Audit**: Security violations (401/403) are logged with high severity.

## 6. Circuit Breakers
- **Function**: Protect external provider availability.
- **Policy**: 5 failures -> OPEN state for 60 seconds.
- **Result**: Immediate `503 Service Unavailable` returned to prevent request piling.
