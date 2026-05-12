# API Interface Contracts — v1

## 1. Overview
This document freezes the public API surfaces of the MemLayer runtime. Any changes to these contracts must follow the versioning policy defined in the Runtime Specification.

## 2. Global Headers
| Header | Description | Required |
| :--- | :--- | :--- |
| `Authorization` | `Bearer <JWT>` | Yes (Default) |
| `X-API-Key` | Infrastructure Access Key | Yes (Alternative) |
| `X-Trace-Id` | Unique Correlation ID | Optional (Auto-generated) |
| `X-Tenant-Id` | Overriding Tenant ID | Only for `platform_admin` |

## 3. Workspace API (`/api/workspaces`)
### 3.1. Create Workspace
- **POST** `/`
- **Payload**: `{"name": string, "description": string}`
- **Immutable Result**: `{"id": "ws_...", "tenant_id": string, "created_at": iso8601}`

### 3.2. Get Workspace State
- **GET** `/{workspace_id}`
- **Guarantee**: Returns current `memory_count` and `last_checkpoint_id`.

## 4. Memory API (`/api/memories`)
### 4.1. Ingest Memory
- **POST** `/`
- **Payload**: `{"workspace_id": string, "content": string, "metadata": dict}`
- **Deterministic Outcome**: Generates a `memory_id` based on content hash.

## 5. Replay API (`/api/replays`)
### 5.1. Hydrate Trace
- **GET** `/{trace_id}`
- **Guarantee**: Returns the complete execution plan with **Replay Integrity Hash**.

## 6. Constraints & Guarantees
- **JSON Consistency**: All responses use camelCase or snake_case as per schema (snake_case preferred for internal substrate).
- **Error Consistency**: All errors return `{"detail": string, "error_code": string, "trace_id": string}`.
- **Async Safety**: Mutation endpoints return 202 Accepted if the operation is backgrounded, but must ensure eventual consistency within the `Unit of Work` boundaries.

## 7. Forbidden Modifications
- Changing the data type of `id` fields (Must remain `String/UUID`).
- Removing `tenant_id` from response payloads.
- Altering the default status codes for success (200/201).
