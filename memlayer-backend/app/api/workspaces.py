"""
API routes for workspace management.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.workspace import WorkspaceService
from app.schemas.memory import WorkspaceResponse, ChatResponse
from typing import List

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse)
def create_workspace(
    name: str,
    description: str = None,
    db: Session = Depends(get_db),
):
    """Create a new workspace."""
    service = WorkspaceService(db)
    workspace = service.create_workspace(name=name, description=description)
    return workspace


@router.get("", response_model=List[WorkspaceResponse])
def list_workspaces(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all workspaces."""
    service = WorkspaceService(db)
    workspaces = service.list_workspaces(limit=limit, offset=offset)
    return workspaces


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific workspace."""
    service = WorkspaceService(db)
    workspace = service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.delete("/{workspace_id}")
def delete_workspace(
    workspace_id: str,
    db: Session = Depends(get_db),
):
    """Delete a workspace."""
    service = WorkspaceService(db)
    success = service.delete_workspace(workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"message": "Workspace deleted"}


@router.post("/{workspace_id}/chats", response_model=ChatResponse)
def create_chat(
    workspace_id: str,
    title: str = None,
    db: Session = Depends(get_db),
):
    """Create a new chat in a workspace."""
    service = WorkspaceService(db)
    workspace = service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    chat = service.create_chat(workspace_id, title)
    return chat


@router.get("/{workspace_id}/chats", response_model=List[ChatResponse])
def list_chats(
    workspace_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List chats in a workspace."""
    service = WorkspaceService(db)
    workspace = service.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    chats = service.list_chats(workspace_id, limit=limit, offset=offset)
    return chats
