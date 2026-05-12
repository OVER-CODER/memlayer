# Snapshot & Object Storage Architecture — Durable State Recovery

## 1. Overview
The Snapshot Architecture manages large-scale, durable recovery points for MemLayer workspaces. While relational data resides in PostgreSQL, the "heavy" state (memories, embeddings, large traces) is managed through an Object Storage abstraction layer.

## 2. Storage Abstraction Layer
MemLayer uses a provider-agnostic `ObjectStorageService` interface:
- **Local Mode**: Stores files in `.memlayer/snapshots/` (for Dev/Test).
- **Cloud Mode**: Supports S3, GCS, Azure Blob, and MinIO (for Production).

## 3. Snapshot Composition
A "Snapshot" is a compressed archive containing:
1.  `workspace_metadata.json`: Name, configs, tenant info.
2.  `semantic_memory_dump.jsonl`: All memories in the workspace at the time of snapshot.
3.  `lineage_manifest.json`: The ancestry graph up to the current checkpoint.
4.  `integrity_checksums.txt`: SHA256 hashes of all components.

## 4. Operational Workflows

### 4.1. Scheduled Snapshots
The `SnapshotEngine` periodically (e.g., every 100 turns or 24 hours) triggers a background backup of the workspace state to object storage.

### 4.2. Recovery & Restoration
1.  Operator selects a snapshot from the Console.
2.  System downloads the archive from Object Storage.
3.  `RecoveryManager` validates checksums.
4.  Data is re-hydrated into PostgreSQL.
5.  Runtime re-initializes from the last snapshotted `checkpoint_id`.

### 4.3. Workspace Branching
Snapshots are the basis for branching. A new workspace can be initialized from an existing snapshot, creating a parallel "Timeline" for experimentation without affecting the source lineage.

## 5. Security & Isolation
- **Tenant-Scoped Buckets**: In high-security modes, each tenant uses a separate storage bucket.
- **Encryption at Rest**: All snapshots are encrypted using provider-managed keys (SSE) or client-side encryption.
- **Signed URLs**: The Operational Console uses time-limited signed URLs to securely download snapshots directly from the object store.

## 6. Implementation Checklist
- [ ] Implement `IObjectStorageProvider` interface.
- [ ] Implement `LocalFileSystemProvider`.
- [ ] Implement `AWSS3Provider` using `boto3` or `aiobotocore`.
- [ ] Add `snapshot_metadata` to the `workspaces` table to track availability.
