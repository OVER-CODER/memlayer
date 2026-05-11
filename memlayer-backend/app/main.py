"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import workspaces, chats, memories
from app.db.session import init_db
from app.core.config import settings

# Initialize database
init_db()

# Create app
app = FastAPI(
    title="MemLayer - Persistent Semantic Memory Runtime",
    description="Foundational memory system for AI workspaces",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workspaces.router)
app.include_router(chats.router)
app.include_router(memories.router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/api/config")
def get_config():
    """Get system configuration."""
    return {
        "embedding_model": settings.embedding_model,
        "embedding_dim": settings.embedding_dim,
        "gemini_model": settings.gemini_model,
        "top_k_memories": settings.top_k_memories,
        "memory_retrieval_threshold": settings.memory_retrieval_threshold,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
