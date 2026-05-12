"""
Redis-backed Runtime Coordination Layer for MemLayer.
Provides ephemeral state synchronization, distributed locking, and projection caching.
Includes graceful degradation when Redis is unavailable.
"""

import json
import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

# Lazy import to allow graceful degradation
_redis = None
_redis_available = None


def _get_redis_client():
    """Lazy initialization of Redis client with graceful handling."""
    global _redis, _redis_available

    if _redis_available is False:
        return None

    if _redis is None:
        try:
            import redis
            from app.core.config import settings

            if settings.redis_url:
                _redis = redis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
            else:
                _redis = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
            # Test connection
            _redis.ping()
            _redis_available = True
            logger.info("✓ Redis connection established")
        except Exception as e:
            logger.warning(f"⚠ Redis unavailable - running in degraded mode: {e}")
            _redis_available = False
            _redis = None

    return _redis


class RuntimeCoordinationLayer:
    """
    Operational coordination layer using Redis.

    Responsibilities:
    - Distributed Locking (preventing concurrent workspace corruption)
    - Ephemeral Projection Caching (reducing compiler overhead)
    - Agent Session Synchronization

    Gracefully degrades when Redis is unavailable.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        """Lazy load Redis client."""
        if self._client is None:
            self._client = _get_redis_client()
        return self._client

    def _get_key(self, tenant_id: str, prefix: str, key_id: str) -> str:
        """Deterministic tenant-isolated key generation."""
        return f"{tenant_id}:{prefix}:{key_id}"

    def is_available(self) -> bool:
        """Check if Redis is currently available."""
        return self.client is not None

    def acquire_lock(
        self, tenant_id: str, lock_id: str, owner_id: str, timeout: int = 30
    ) -> bool:
        """Acquire a distributed lock with ownership validation."""
        if not self.client:
            logger.warning("Redis unavailable - lock acquisition denied")
            return False

        try:
            key = self._get_key(tenant_id, "lock", lock_id)
            return self.client.set(key, owner_id, ex=timeout, nx=True)
        except Exception as e:
            logger.warning(f"Lock acquisition failed: {e}")
            return False

    def release_lock(self, tenant_id: str, lock_id: str, owner_id: str) -> bool:
        """Release a distributed lock only if owned by the caller."""
        if not self.client:
            logger.warning("Redis unavailable - lock release denied")
            return False

        try:
            key = self._get_key(tenant_id, "lock", lock_id)
            current_owner = self.client.get(key)
            if current_owner == owner_id:
                self.client.delete(key)
                return True
            return False
        except Exception as e:
            logger.warning(f"Lock release failed: {e}")
            return False

    def cache_projection(
        self, tenant_id: str, projection_id: str, data: Dict[str, Any], ttl: int = 3600
    ) -> None:
        """Cache a compiled projection with tenant isolation."""
        if not self.client:
            logger.debug("Redis unavailable - skipping projection cache")
            return

        try:
            key = self._get_key(tenant_id, "projection", projection_id)
            self.client.set(key, json.dumps(data), ex=ttl)
        except Exception as e:
            logger.warning(f"Projection cache failed: {e}")

    def get_projection(
        self, tenant_id: str, projection_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a cached projection for a specific tenant."""
        if not self.client:
            return None

        try:
            key = self._get_key(tenant_id, "projection", projection_id)
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Projection retrieval failed: {e}")
            return None

    def set_session_state(
        self, tenant_id: str, session_id: str, state: Dict[str, Any], ttl: int = 3600
    ) -> None:
        """Store ephemeral session state with tenant isolation."""
        if not self.client:
            logger.debug("Redis unavailable - skipping session state")
            return

        try:
            key = self._get_key(tenant_id, "session", session_id)
            self.client.set(key, json.dumps(state), ex=ttl)
        except Exception as e:
            logger.warning(f"Session state storage failed: {e}")

    def get_session_state(
        self, tenant_id: str, session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve ephemeral session state for a specific tenant."""
        if not self.client:
            return None

        try:
            key = self._get_key(tenant_id, "session", session_id)
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            logger.warning(f"Session state retrieval failed: {e}")
            return None

    def health_check(self) -> bool:
        """Check Redis connectivity."""
        return self.is_available()


_coordination_layer: Optional[RuntimeCoordinationLayer] = None


def get_coordination_layer() -> RuntimeCoordinationLayer:
    """Get the global coordination layer instance."""
    global _coordination_layer
    if _coordination_layer is None:
        _coordination_layer = RuntimeCoordinationLayer()
    return _coordination_layer
