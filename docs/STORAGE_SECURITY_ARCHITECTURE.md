# Storage Security Architecture — Durable Blob Protection

## 1. Overview
The Storage Security layer ensures that long-lived cognition artifacts (snapshots, archives, replay traces) are stored securely and remain tamper-proof throughout their lifecycle.

## 2. Tenant Path Isolation
Every object stored in the Object Storage substrate (S3, MinIO, or Local) is logically partitioned by its `tenant_id`:
- **Pattern**: `/{tenant_id}/{workspace_id}/{object_type}/{object_id}`
- **Enforcement**: The `IObjectStorageProvider` interface now requires a `tenant_id` for all operations, and implementations automatically prefix the key.
- **Result**: Even if the storage backend is shared, one tenant can never list or download another tenant's objects.

## 3. Snapshot Integrity (SHA256 Manifest)
Snapshots are protected by a signed manifest:
- **Manifest**: Contains SHA256 hashes of all memory blobs and lineage checkpoints.
- **Verification**: During restoration, the system recalculates the hashes of the re-hydrated data and compares them against the manifest.
- **Fail-Safe**: If any byte has been tampered with or corrupted, the restoration process is aborted immediately, preserving the "Integrity Invariant."

## 4. Replay Trace Encryption (Optional/Production)
For high-security environments:
- Replay traces can be encrypted using a tenant-specific key (AES-256) before being uploaded to cold storage.
- **Current Status**: Implemented as a post-processing hook in the `ReplayEngine`.

## 5. Export Security
Exporting a workspace (e.g., for portable cognition) is a privileged operation:
- **Requirement**: `snapshot:restore` permission.
- **Audit**: Every export event is logged in the `GovernanceAudit` trail with a link to the authorized `subject_id`.

## 6. Verification Results

| Scenario | Result | Status |
| :--- | :--- | :--- |
| **Direct Path Traversal** | Blocked (Prefix Isolation) | **PASSED** |
| **Snapshot Corruption** | Detected (Hash Mismatch) | **PASSED** |
| **Unauthorized Download** | Blocked (RBAC Check) | **PASSED** |

## 7. Conclusion
Storage Security provides the "Cold Trust" required for durable cognition. It ensures that the historical state of an agent is just as secure and verifiable as its live runtime state.
