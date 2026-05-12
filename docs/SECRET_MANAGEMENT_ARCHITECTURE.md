# Secret Management Architecture — Runtime Credential Hardening

## 1. Overview
The Secret Management system ensures that sensitive credentials and organizational secrets are protected throughout the cognition lifecycle. It prevents accidental exposure in telemetry, logs, and replay traces.

## 2. Redaction Strategy
MemLayer employs a "Redact-at-Edge" strategy for all observability artifacts:
- **Telemetry Redaction**: Before a `UnifiedCognitionTrace` is persisted, all dictionaries are recursively scanned for sensitive keys (e.g., `api_key`, `token`).
- **Log Masking**: Custom logging filters mask known secrets (loaded from environment variables) and common patterns (e.g., Bearer tokens).
- **Replay Scrubbing**: Historical execution plans are scrubbed of any provider-specific credentials before being committed to the `replay_traces` table.

## 3. Configuration Security
- **Environment Isolation**: Secrets are never hardcoded and are exclusively loaded via `pydantic-settings` from the environment or secure `.env` files.
- **Encrypted Storage**: Production deployments should utilize a dedicated Secret Manager (e.g., AWS Secrets Manager, HashiCorp Vault). MemLayer provides a hook in `app/security/config_security.py` to integrate these providers.

## 4. Protected Subsystems

| Subsystem | Protection Mechanism |
| :--- | :--- |
| **LLM Providers** | API keys redacted from prompt/response traces. |
| **Persistence** | Database credentials masked in connection logs. |
| **Coordination** | Redis passwords excluded from health check metrics. |
| **Object Storage**| S3 Secret Keys never stored in snapshot manifests. |

## 5. Security Invariants
- **NEVER** log a raw secret key.
- **NEVER** persist unencrypted provider credentials in the `Workspaces` table.
- **ALWAYS** use the `SecretManager.redact_dict()` helper when serializing metadata for external export.

## 6. Implementation Example
```python
from app.security.secrets import get_secret_manager

secrets = get_secret_manager()
safe_trace_data = secrets.redact_dict(raw_trace_data)
# Persist safe_trace_data to DB
```
