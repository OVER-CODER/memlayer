"""
API Key Management for MemLayer Security.
Handles long-lived infrastructure access keys.
"""

import secrets
import hashlib
from typing import Optional, Tuple
from app.core.config import settings

class APIKeyManager:
    """Manager for API key generation and hashing."""

    def __init__(self):
        self.salt = settings.secret_key

    def generate_key(self, prefix: str = "ml") -> Tuple[str, str]:
        """
        Generate a new API key and its hash.
        Returns: (raw_key, hashed_key)
        """
        raw_key = f"{prefix}_{secrets.token_urlsafe(32)}"
        hashed_key = self._hash_key(raw_key)
        return raw_key, hashed_key

    def verify_key(self, raw_key: str, hashed_key: str) -> bool:
        """Verify a raw API key against its hash."""
        return secrets.compare_digest(self._hash_key(raw_key), hashed_key)

    def _hash_key(self, key: str) -> str:
        """Deterministic hash of the API key."""
        return hashlib.sha256((key + self.salt).encode()).hexdigest()

_api_key_manager: Optional[APIKeyManager] = None

def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager instance."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
