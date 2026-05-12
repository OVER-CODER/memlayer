"""
JWT Management for MemLayer Security.
Handles deterministic token generation and validation.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from pydantic import BaseModel
from app.core.config import settings

class TokenPayload(BaseModel):
    """Deterministic JWT payload."""
    sub: str  # User ID / Agent ID
    tenant_id: str
    role: str
    exp: datetime
    iat: datetime

class JWTManager:
    """Manager for JWT operations."""

    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24  # 1 day

    def create_access_token(self, subject: str, tenant_id: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
        """Create a new deterministic access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode = {
            "sub": str(subject),
            "tenant_id": tenant_id,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc)
        }
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None

_jwt_manager: Optional[JWTManager] = None

def get_jwt_manager() -> JWTManager:
    """Get global JWT manager instance."""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = JWTManager()
    return _jwt_manager
