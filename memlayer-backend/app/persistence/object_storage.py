"""
Object Storage Infrastructure for MemLayer.
Provides a provider-agnostic interface for durable blobs (snapshots, archives).
"""

import os
import json
import boto3
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, BinaryIO
from botocore.exceptions import ClientError
from app.core.config import settings

logger = logging.getLogger(__name__)


class IObjectStorageProvider(ABC):
    """Interface for durable object storage."""

    @abstractmethod
    async def upload(self, tenant_id: str, key: str, data: BinaryIO, metadata: Optional[Dict] = None) -> bool:
        """Upload a file or blob with tenant isolation."""
        pass

    @abstractmethod
    async def download(self, tenant_id: str, key: str) -> Optional[bytes]:
        """Download a file or blob with tenant isolation."""
        pass

    @abstractmethod
    async def delete(self, tenant_id: str, key: str) -> bool:
        """Delete a file or blob with tenant isolation."""
        pass

    @abstractmethod
    async def list_objects(self, tenant_id: str, prefix: str = "") -> List[str]:
        """List object keys for a specific tenant."""
        pass


class LocalFileSystemProvider(IObjectStorageProvider):
    """Local filesystem implementation (Dev/Test)."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def _get_path(self, tenant_id: str, key: str) -> str:
        return os.path.join(self.base_path, tenant_id, key)

    async def upload(self, tenant_id: str, key: str, data: BinaryIO, metadata: Optional[Dict] = None) -> bool:
        path = self._get_path(tenant_id, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.read())
        if metadata:
            with open(path + ".meta", "w") as f:
                json.dump(metadata, f)
        return True

    async def download(self, tenant_id: str, key: str) -> Optional[bytes]:
        path = self._get_path(tenant_id, key)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    async def delete(self, tenant_id: str, key: str) -> bool:
        path = self._get_path(tenant_id, key)
        if os.path.exists(path):
            os.remove(path)
            if os.path.exists(path + ".meta"):
                os.remove(path + ".meta")
            return True
        return False

    async def list_objects(self, tenant_id: str, prefix: str = "") -> List[str]:
        tenant_path = os.path.join(self.base_path, tenant_id)
        if not os.path.exists(tenant_path):
            return []
        
        keys = []
        for root, _, files in os.walk(tenant_path):
            for file in files:
                if not file.endswith(".meta"):
                    rel_path = os.path.relpath(os.path.join(root, file), tenant_path)
                    if rel_path.startswith(prefix):
                        keys.append(rel_path)
        return keys


class S3StorageProvider(IObjectStorageProvider):
    """AWS S3 / MinIO implementation (Production)."""

    def __init__(
        self, 
        bucket: str, 
        region: str, 
        access_key: Optional[str] = None, 
        secret_key: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        self.bucket = bucket
        self.s3 = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url
        )

    def _get_key(self, tenant_id: str, key: str) -> str:
        return f"{tenant_id}/{key}"

    async def upload(self, tenant_id: str, key: str, data: BinaryIO, metadata: Optional[Dict] = None) -> bool:
        try:
            full_key = self._get_key(tenant_id, key)
            extra_args = {}
            if metadata:
                extra_args["Metadata"] = {k: str(v) for k, v in metadata.items()}
            
            self.s3.upload_fileobj(data, self.bucket, full_key, ExtraArgs=extra_args)
            return True
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False

    async def download(self, tenant_id: str, key: str) -> Optional[bytes]:
        try:
            full_key = self._get_key(tenant_id, key)
            response = self.s3.get_object(Bucket=self.bucket, Key=full_key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return None
            logger.error(f"S3 download failed: {e}")
            return None

    async def delete(self, tenant_id: str, key: str) -> bool:
        try:
            full_key = self._get_key(tenant_id, key)
            self.s3.delete_object(Bucket=self.bucket, Key=full_key)
            return True
        except ClientError as e:
            logger.error(f"S3 delete failed: {e}")
            return False

    async def list_objects(self, tenant_id: str, prefix: str = "") -> List[str]:
        try:
            full_prefix = self._get_key(tenant_id, prefix)
            response = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=full_prefix)
            if "Contents" in response:
                return [obj["Key"].replace(f"{tenant_id}/", "", 1) for obj in response["Contents"]]
            return []
        except ClientError as e:
            logger.error(f"S3 list failed: {e}")
            return []


def get_storage_provider() -> IObjectStorageProvider:
    """Factory to get the configured storage provider."""
    provider_type = settings.storage_provider.lower()
    
    if provider_type == "local":
        return LocalFileSystemProvider(settings.storage_local_path)
    
    if provider_type in ("s3", "minio"):
        return S3StorageProvider(
            bucket=settings.s3_bucket,
            region=settings.s3_region,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            endpoint_url=settings.s3_endpoint_url
        )
    
    raise ValueError(f"Unsupported storage provider: {provider_type}")
