"""
Tenant Propagation Middleware for FastAPI.
Ensures tenant_id is available globally in the request context.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from contextvars import ContextVar

# Global context for tenant isolation
tenant_id_context: ContextVar[str] = ContextVar("tenant_id", default="default")

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to propagate the tenant_id into a ContextVar.
    Allows repositories and services to access the tenant without explicit parameter passing.
    """

    async def dispatch(self, request: Request, call_next):
        if hasattr(request.state, "auth"):
            tenant_id = request.state.auth.tenant_id
            token = tenant_id_context.set(tenant_id)
            try:
                response = await call_next(request)
                return response
            finally:
                tenant_id_context.reset(token)
        else:
            return await call_next(request)

def get_current_tenant() -> str:
    """Helper to get the tenant_id for the current request context."""
    return tenant_id_context.get()
