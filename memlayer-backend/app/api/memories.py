"""
API routes for memory management and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.memory_storage import MemoryStorageService
from app.services.memory_retrieval import MemoryRetrievalService
from app.schemas.memory import (
    MemoryCreate,
    MemoryResponse,
    MemoryStats,
    RetrievalStats,
    RetrievedMemory,
)
from app.security.authentication import AuthContext
from app.api.dependencies import get_auth_context
from typing import List

router = APIRouter(prefix="/api/workspaces/{workspace_id}/memories", tags=["memories"])


@router.post("", response_model=MemoryResponse)
def create_memory(
    workspace_id: str,
    request: MemoryCreate,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Create a new memory (tenant-scoped)."""
    from app.db.models import Workspace

    # Verify workspace exists and belongs to tenant
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .filter(Workspace.tenant_id == auth.tenant_id)
        .first()
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    service = MemoryStorageService(db)
    memory = service.create_memory(
        workspace_id=workspace_id,
        raw_content=request.raw_content,
        source_type=request.source_type,
        summary=request.summary,
        importance_score=request.importance_score,
        metadata=request.metadata,
    )
    return memory


@router.get("", response_model=List[MemoryResponse])
def list_memories(
    workspace_id: str,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """List memories in a workspace (tenant-scoped)."""
    from app.db.models import Workspace

    # Verify workspace exists and belongs to tenant
    workspace = (
        db.query(Workspace)
        .filter(Workspace.id == workspace_id)
        .filter(Workspace.tenant_id == auth.tenant_id)
        .first()
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    service = MemoryStorageService(db)
    memories = service.list_workspace_memories(workspace_id, limit, offset)
    return memories


@router.get("/search", response_model=List[RetrievedMemory])
def search_memories(
    workspace_id: str,
    query: str,
    top_k: int = 5,
    similarity_threshold: float = 0.3,
    db: Session = Depends(get_db),
):
    """Search for semantically similar memories."""
    from app.db.models import Workspace

    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    service = MemoryRetrievalService(db)
    memories, scores = service.retrieve(
        workspace_id=workspace_id,
        query=query,
        top_k=top_k,
        similarity_threshold=similarity_threshold,
    )

    return [
        {
            "id": m.id,
            "content": m.raw_content,
            "summary": m.summary,
            "source_type": m.source_type,
            "similarity_score": s,
            "importance_score": m.importance_score,
            "timestamp": m.timestamp,
        }
        for m, s in zip(memories, scores)
    ]


@router.get("/{memory_id}", response_model=MemoryResponse)
def get_memory(
    workspace_id: str,
    memory_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific memory."""
    from app.db.models import Workspace, Memory

    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    service = MemoryStorageService(db)
    memory = service.get_memory(memory_id)
    if not memory or memory.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Memory not found")

    return memory


@router.delete("/{memory_id}")
def delete_memory(
    workspace_id: str,
    memory_id: str,
    db: Session = Depends(get_db),
):
    """Delete a memory."""
    from app.db.models import Workspace, Memory

    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Verify memory belongs to workspace
    memory = db.query(Memory).filter(Memory.id == memory_id).first()
    if not memory or memory.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Memory not found")

    service = MemoryStorageService(db)
    success = service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {"message": "Memory deleted"}


@router.get("/stats/memories", response_model=MemoryStats)
def get_memory_stats(
    workspace_id: str,
    db: Session = Depends(get_db),
):
    """Get memory statistics."""
    from app.db.models import Workspace

    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    service = MemoryStorageService(db)
    stats = service.get_memory_stats(workspace_id)
    return stats


@router.get("/stats/retrievals", response_model=RetrievalStats)
def get_retrieval_stats(
    workspace_id: str,
    db: Session = Depends(get_db),
):
    """Get retrieval statistics."""
    from app.db.models import Workspace

    # Verify workspace exists
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    service = MemoryRetrievalService(db)
    stats = service.get_retrieval_stats(workspace_id)
    return stats
