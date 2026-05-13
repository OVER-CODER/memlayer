"""
Dependencies for extracting authentication context in API endpoints.
"""

from fastapi import Depends, Request, HTTPException
from app.security.authentication import AuthContext


def get_auth_context(request: Request) -> AuthContext:
    """
    Extract auth context from request state (set by AuthenticationMiddleware).

    Usage:
        @router.get("/endpoint")
        def my_endpoint(auth: AuthContext = Depends(get_auth_context)):
            print(f"User: {auth.subject}, Tenant: {auth.tenant_id}")
    """
    auth = getattr(request.state, "auth", None)
    if not auth:
        raise HTTPException(status_code=401, detail="Authentication required")
    return auth


def get_tenant_id(request: Request) -> str:
    """Extract just the tenant_id from auth context."""
    auth = get_auth_context(request)
    return auth.tenant_id


def require_role(required_role: str):
    """Dependency to require a specific role."""

    def role_checker(auth: AuthContext = Depends(get_auth_context)):
        if auth.role != required_role and "admin" not in auth.role:
            raise HTTPException(
                status_code=403, detail=f"Role '{required_role}' required"
            )
        return auth

    return role_checker
