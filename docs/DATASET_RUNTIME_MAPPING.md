# Dataset Runtime Mapping — Cognition Substrate Injection

## 1. Overview
This document defines the deterministic mapping of the LoCoMo and MSC datasets into the MemLayer runtime infrastructure. These mappings ensure that dataset ingestion is reproducible and replay-safe.

## 2. LoCoMo → Longitudinal Runtime Mapping

| Dataset Field | MemLayer Component | Mapping Logic |
| :--- | :--- | :--- |
| `sample_id` | **Workspace ID** | `ws_locomo_{sample_id}` |
| `speaker_a/b` | **Agent Context** | User vs. Assistant roles in the runtime. |
| `session_X` | **Semantic Checkpoint**| Each session is ingested as an atomic turn block. |
| `session_X_date_time`| **Lineage Timestamp** | Normalized to ISO 8601 UTC. |
| `dia_id` | **Memory Hash Seed** | Used for deterministic identity hashing. |
| `text` | **Raw Content** | Ingested via the `SemanticChunker`. |

### Ingestion Flow:
1.  Initialize Workspace `ws_locomo_conv_1`.
2.  Iterate through sessions 1 to N.
3.  For each session:
    - Create a `SemanticLineage` checkpoint.
    - Ingest each utterance as a `SemanticMemory`.
    - Record a `ReplayTrace` for the session ingestion.
    - (Optional) Trigger a `WorkspaceSummary` update.

## 3. MSC → Concurrency Runtime Mapping (If Available)

| Dataset Field | MemLayer Component | Mapping Logic |
| :--- | :--- | :--- |
| `conversation_id` | **Workspace ID** | `ws_msc_{id}` |
| `turn_id` | **Sequence Number** | Enforces deterministic message ordering. |
| `text` | **Raw Content** | Concurrent stream ingestion. |

### Ingestion Flow:
1.  Initialize 100+ parallel Workspaces.
2.  Stream turns into the `CoordinationRuntime`.
3.  Stress-test `Redis` locks on overlapping `conversation_id` ingestion.
4.  Verify `pgvector` indexing throughput.

## 4. Deterministic Identity Generation
To ensure replayability, all identifiers created during ingestion must be derived deterministically:
- `memory_id = SHA256(ws_id + dia_id + text)`
- `checkpoint_id = SHA256(ws_id + session_id + timestamp)`

## 5. Metadata Enrichment
Extra metadata from LoCoMo (e.g., `qa_pairs`) will be stored in the `Workspace.extra_metadata` field to enable automated ground-truth verification after ingestion.
