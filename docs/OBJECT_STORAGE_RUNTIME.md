# Object Storage Infrastructure — Durable Cognition Archives

## 1. Overview
The Object Storage layer provides a provider-agnostic durable substrate for large-scale cognition artifacts, including snapshots, replay archives, and governance exports.

## 2. Infrastructure Components

### 2.1. Provider Abstraction
MemLayer implements the `IObjectStorageProvider` interface, allowing the runtime to switch between local development and cloud production without code changes.

### 2.2. Supported Providers
- **LocalFileSystemProvider**: Uses the local disk (`./.memlayer/storage`) for dev/test environments.
- **S3StorageProvider**: Integrates with **AWS S3** or **MinIO** for production and high-availability scenarios.

## 3. Runtime Integration

### 3.1. Snapshots
Snapshots are serialized as compressed JSON archives and uploaded to the `memlayer-snapshots` bucket. Every snapshot is verified against a SHA256 manifest before being accepted as a valid recovery point.

### 3.2. Replay Archives
High-volume replay traces that exceed the database's warm-storage limit are archived to Object Storage. The `ReplayEngine` can dynamically re-hydrate these traces by downloading the corresponding blob.

## 4. Operational Guarantees

- **Integrity**: Every uploaded object includes its MD5/SHA256 checksum in the metadata.
- **Isolation**: Tenant data is separated by key prefixes (e.g., `tenant-123/snapshots/ws-456.zip`).
- **Persistence**: All object storage operations are asynchronous but return deterministic completion status.

## 5. Deployment Topology (MinIO)
In the local production stack (`docker-compose`), **MinIO** provides an S3-compatible API, allowing for bit-for-bit identical testing of the cloud-native storage flow.

## 6. Implementation Checklist
- [x] Define `IObjectStorageProvider` contract.
- [x] Implement `LocalFileSystemProvider`.
- [x] Implement `S3StorageProvider` (boto3).
- [x] Integrate with `docker-compose` topology.
