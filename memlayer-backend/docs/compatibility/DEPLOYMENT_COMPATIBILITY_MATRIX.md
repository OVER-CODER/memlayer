# Deployment Compatibility Matrix — v1

## 1. Supported Software Stack

| Component | Version | Role |
| :--- | :--- | :--- |
| **Python** | 3.11+ | Primary Runtime |
| **PostgreSQL**| 15+ | Persistence Substrate |
| **pgvector** | 0.5.0+ | Semantic Vector Ops |
| **Redis** | 6.2+ | Coordination Substrate |
| **MinIO** | Latest | S3-Compatible Storage |
| **Docker** | 24.0+ | Containerized Deployment|
| **Alpine** | 3.18+ | Base Image |

## 2. Infrastructure Requirements

### 2.1. Minimum Hardware (Development)
- **CPU**: 2 Cores.
- **RAM**: 2 GB.
- **Storage**: 10 GB.

### 2.2. Recommended (Production - Medium Load)
- **CPU**: 4-8 Cores (Optimized for JSON/Hash processing).
- **RAM**: 8-16 GB (Index residency in Postgres).
- **Network**: Low latency (< 10ms) between App, DB, and Redis.

## 3. Storage Provider Support
- **Local**: Development only.
- **S3**: Official production target.
- **MinIO**: S3-compatible production target.
- **GCS**: Supported via S3-interoperability mode.

## 4. Scaling Assumptions
- **Horizontal**: App workers can scale horizontally behind a load balancer.
- **Vertical**: PostgreSQL/pgvector requires vertical scaling or partitioning for > 10M memories.
- **Coordination**: Redis Cluster recommended for global multi-region deployments.

## 5. Security Environment
- **HTTPS**: Required for all production API traffic.
- **VPC**: App, DB, and Redis should reside in a private subnet.
- **IAM**: Least-privilege roles for S3/Object Storage access.
