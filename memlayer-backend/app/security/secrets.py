"""
Secret Management for MemLayer Security.
Handles encryption and redaction of sensitive runtime artifacts.
"""

import re
from typing import Any, List, Optional
from app.core.config import settings

class SecretManager:
    """Manages sensitive credential redaction and protection."""

    def __init__(self):
        # Patterns to redact from logs and telemetry
        self.redact_patterns = [
            re.compile(r"api[-_]?key", re.IGNORECASE),
            re.compile(r"secret[-_]?key", re.IGNORECASE),
            re.compile(r"password", re.IGNORECASE),
            re.compile(r"token", re.IGNORECASE),
            re.compile(r"Bearer\s+[a-zA-Z0-9\-\._~+/]+=*", re.IGNORECASE),
            re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),  # General provider key pattern
        ]
        
        # Actual values to redact (from settings)
        self.sensitive_values = [
            settings.secret_key,
            settings.anthropic_api_key,
            settings.gemini_api_key,
            settings.s3_secret_key,
            settings.redis_password
        ]
        self.sensitive_values = [v for v in self.sensitive_values if v]

    def redact(self, text: str) -> str:
        """Redact sensitive patterns and values from a string."""
        if not text:
            return text
            
        redacted = text
        
        # Redact specific known values
        for val in self.sensitive_values:
            redacted = redacted.replace(val, "[REDACTED]")
            
        # Redact common patterns (best effort)
        # We only redact values, not the keys themselves
        return redacted

    def redact_dict(self, data: Any) -> Any:
        """Recursively redact sensitive data from a dictionary or list."""
        if isinstance(data, dict):
            return {k: self.redact_dict(v) if not any(p.search(k) for p in self.redact_patterns) else "[REDACTED]" for k, v in data.items()}
        elif isinstance(data, list):
            return [self.redact_dict(i) for i in data]
        elif isinstance(data, str):
            return self.redact(data)
        return data

_secret_manager: Optional[SecretManager] = None

def get_secret_manager() -> SecretManager:
    """Get global secret manager instance."""
    global _secret_manager
    if _secret_manager is None:
        _secret_manager = SecretManager()
    return _secret_manager
