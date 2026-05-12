"""
Redis-backed Runtime Coordination Layer for MemLayer.
Provides ephemeral state synchronization, distributed locking, and projection caching.
"""

import json
import redis
import logging
from typing import Optional, Any, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)


class RuntimeCoordinationLayer:
    """
    Operational coordination layer using Redis.
    
    Responsibilities:
    - Distributed Locking (preventing concurrent workspace corruption)
    - Ephemeral Projection Caching (reducing compiler overhead)
    - Agent Session Synchronization
    """

    def __init__(self):
        self._redis = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password,
            decode_responses=True
        )

    def _get_key(self, tenant_id: str, prefix: str, key_id: str) -> str:
        """Deterministic tenant-isolated key generation."""
        return f"{tenant_id}:{prefix}:{key_id}"

    def acquire_lock(self, tenant_id: str, lock_id: str, owner_id: str, timeout: int = 30) -> bool:
        """Acquire a distributed lock with ownership validation."""
        key = self._get_key(tenant_id, "lock", lock_id)
        return self._redis.set(key, owner_id, ex=timeout, nx=True)

    def release_lock(self, tenant_id: str, lock_id: str, owner_id: str) -> bool:
        """Release a distributed lock only if owned by the caller."""
        key = self._get_key(tenant_id, "lock", lock_id)
        current_owner = self._redis.get(key)
        if current_owner == owner_id:
            self._redis.delete(key)
            return True
        return False

    def cache_projection(self, tenant_id: str, projection_id: str, data: Dict[str, Any], ttl: int = 3600) -> None:
        """Cache a compiled projection with tenant isolation."""
        key = self._get_key(tenant_id, "projection", projection_id)
        self._redis.set(key, json.dumps(data), ex=ttl)

    def get_projection(self, tenant_id: str, projection_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached projection for a specific tenant."""
        key = self._get_key(tenant_id, "projection", projection_id)
        data = self._redis.get(key)
        return json.loads(data) if data else None

    def set_session_state(self, tenant_id: str, session_id: str, state: Dict[str, Any], ttl: int = 3600) -> None:
        """Store ephemeral session state with tenant isolation."""
        key = self._get_key(tenant_id, "session", session_id)
        self._redis.set(key, json.dumps(state), ex=ttl)

    def get_session_state(self, tenant_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve ephemeral session state for a specific tenant."""
        key = self._get_key(tenant_id, "session", session_id)
        data = self._redis.get(key)
        return json.loads(data) if data else None

    def health_check(self) -> bool:
        """Check Redis connectivity."""
        try:
            return self._redis.ping()
        except Exception:
            return False


_coordination_layer: Optional[RuntimeCoordinationLayer] = None


def get_coordination_layer() -> RuntimeCoordinationLayer:
    """Get the global coordination layer instance."""
    global _coordination_layer
    if _coordination_layer is None:
        _coordination_layer = RuntimeCoordinationLayer()
    return _coordination_layer
