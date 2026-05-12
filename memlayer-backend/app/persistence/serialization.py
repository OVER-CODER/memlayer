"""
Deterministic Serialization Layer for MemLayer Persistence.

Ensures that all cognition data is serialized in a stable, canonical form
to preserve checksum integrity and replay determinism.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib


class CanonicalSerializer:
    """
    Enforces deterministic serialization of Python objects.
    
    Principles:
    - Stable key ordering (sort_keys=True)
    - Stable timestamp formatting (ISO 8601 UTC)
    - Stable float precision (optional, if needed)
    - Removal of non-essential whitespace
    """

    @staticmethod
    def to_json(data: Any) -> str:
        """Serialize data to a deterministic JSON string."""
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            default=CanonicalSerializer._json_default
        )

    @staticmethod
    def to_dict(data: Any) -> Dict[str, Any]:
        """Convert data to a deterministic dictionary by serializing and deserializing."""
        # This ensures that any non-standard types are converted to stable JSON types
        return json.loads(CanonicalSerializer.to_json(data))

    @staticmethod
    def compute_checksum(data: Any) -> str:
        """Compute SHA-256 checksum of canonical JSON representation."""
        json_str = CanonicalSerializer.to_json(data)
        return hashlib.sha256(json_str.encode()).hexdigest()

    @staticmethod
    def _json_default(obj: Any) -> Any:
        """Handle non-standard types for JSON serialization."""
        if isinstance(obj, (datetime,)):
            # Force UTC and ISO 8601 format
            if obj.tzinfo is None:
                obj = obj.replace(tzinfo=timezone.utc)
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)


def get_canonical_serializer() -> CanonicalSerializer:
    """Get the global canonical serializer."""
    return CanonicalSerializer()
