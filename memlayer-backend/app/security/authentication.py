"""
Authentication Context for MemLayer Security.
Provides the immutable identity for the request lifecycle.
"""

from typing import Optional
from pydantic import BaseModel, Field

class AuthContext(BaseModel):
    """Immutable identity for the request lifecycle."""
    subject: str = Field(..., description="User or Agent ID")
    tenant_id: str = Field(..., description="Owner Tenant ID")
    role: str = Field(..., description="Assigned RBAC role")
    auth_type: str = Field(..., description="Method of authentication (jwt, api_key)")

    class Config:
        frozen = True  # Ensure immutability
