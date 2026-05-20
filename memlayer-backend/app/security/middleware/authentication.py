"""
Authentication Middleware for FastAPI.
Extracts identity and tenant context from request headers.
"""

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.security.jwt_manager import get_jwt_manager
from app.security.api_keys import get_api_key_manager
from app.security.authentication import AuthContext

# Paths that don't require authentication
PUBLIC_PATHS = [
    "/health",
    "/health/ready",
    "/metrics",
    "/api/config",
    "/docs",
    "/openapi.json",
    "/redoc",
]


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to resolve AuthContext for every request.
    Supports JWT (Bearer) and API Key (X-API-Key) headers.
    """

    async def dispatch(self, request: Request, call_next):
        # Expose health and config endpoints (no auth required)
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        api_key_header = request.headers.get("X-API-Key")

        auth_context: Optional[AuthContext] = None

        # 1. Try JWT
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = get_jwt_manager().decode_token(token)
            if payload:
                tenant_id = request.headers.get("X-Tenant-ID") or payload.get("tenant_id", "default")
                auth_context = AuthContext(
                    subject=payload["sub"],
                    tenant_id=tenant_id,
                    role=payload["role"],
                    auth_type="jwt",
                )

        # 2. Try API Key (Simplified for Phase C, would normally check DB)
        elif api_key_header:
            # Placeholder: In production, verify against SQLAuditRepository or a dedicated APIKey store
            # For now, we simulate a valid key if it matches a development pattern
            if api_key_header.startswith("ml_dev_"):
                tenant_id = request.headers.get("X-Tenant-ID") or "default"
                auth_context = AuthContext(
                    subject="dev_agent",
                    tenant_id=tenant_id,
                    role="developer",
                    auth_type="api_key",
                )

        if not auth_context:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authentication"},
            )

        # Attach to request state
        request.state.auth = auth_context

        response = await call_next(request)
        return response
