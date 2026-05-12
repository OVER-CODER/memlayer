"""
Workspace management service.
"""

from sqlalchemy.orm import Session
from app.db.models import Workspace, Chat
from typing import List, Optional
import uuid
from datetime import datetime, timezone


class WorkspaceService:
    """Manages workspace creation and management."""

    def __init__(self, db: Session):
        self.db = db

    def create_workspace(
        self,
        name: str,
        description: Optional[str] = None,
    ) -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def get_workspace(self, workspace_id: str) -> Optional[Workspace]:
        """Get workspace by ID."""
        return self.db.query(Workspace).filter(Workspace.id == workspace_id).first()

    def list_workspaces(self, limit: int = 100, offset: int = 0) -> List[Workspace]:
        """List all workspaces."""
        return (
            self.db.query(Workspace)
            .order_by(Workspace.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete_workspace(self, workspace_id: str) -> bool:
        """Delete a workspace and all associated data."""
        workspace = self.get_workspace(workspace_id)
        if workspace:
            self.db.delete(workspace)
            self.db.commit()
            return True
        return False

    def create_chat(self, workspace_id: str, title: Optional[str] = None) -> Chat:
        """Create a new chat in a workspace."""
        chat = Chat(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            title=title or f"Chat {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)
        return chat

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get chat by ID."""
        return self.db.query(Chat).filter(Chat.id == chat_id).first()

    def list_chats(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Chat]:
        """List chats in a workspace."""
        return (
            self.db.query(Chat)
            .filter(Chat.workspace_id == workspace_id)
            .order_by(Chat.updated_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat."""
        chat = self.get_chat(chat_id)
        if chat:
            self.db.delete(chat)
            self.db.commit()
            return True
        return False
