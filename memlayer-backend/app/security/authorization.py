"""
Authorization Engine for MemLayer Security.
Enforces RBAC and tenant-scoped access.
"""

from typing import List
from fastapi import HTTPException, status
from app.security.authentication import AuthContext
from app.security.rbac import Role, Permission, ROLE_PERMISSIONS

class AuthorizationEngine:
    """Deterministic authorization evaluator."""

    @staticmethod
    def check_permission(auth: AuthContext, required_permission: Permission):
        """Check if the current identity has a specific permission."""
        role = Role(auth.role)
        permissions = ROLE_PERMISSIONS.get(role, set())
        
        if required_permission not in permissions and Permission.PLATFORM_ADMIN not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Identity {auth.subject} lacks required permission: {required_permission}"
            )

    @staticmethod
    def verify_tenant_access(auth: AuthContext, target_tenant_id: str):
        """Ensure the identity is operating within its authorized tenant."""
        if auth.tenant_id != target_tenant_id and Role(auth.role) != Role.PLATFORM_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Identity {auth.subject} is not authorized for tenant {target_tenant_id}"
            )
