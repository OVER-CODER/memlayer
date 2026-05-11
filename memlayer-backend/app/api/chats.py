"""
API routes for chat and message handling.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.chat_orchestration import ChatOrchestrationService
from app.schemas.memory import ChatQueryRequest, ChatQueryResponse, MessageResponse
from typing import List

router = APIRouter(prefix="/api/chats", tags=["chats"])


@router.post("/{chat_id}/query", response_model=ChatQueryResponse)
def query_chat(
    chat_id: str,
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Send a message to a chat.

    Processes through the complete pipeline:
    1. Retrieve relevant semantic memories
    2. Compile context
    3. Generate LLM response
    4. Store memories
    """
    from app.db.models import Chat

    # Verify chat exists
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    try:
        service = ChatOrchestrationService(db)
        result = service.process_message(
            workspace_id=chat.workspace_id,
            chat_id=chat_id,
            query=request.query,
            top_k_memories=request.top_k_memories,
            similarity_threshold=request.similarity_threshold,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing message: {str(e)}"
        )


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Get messages from a chat."""
    from app.db.models import Chat, Message

    # Verify chat exists
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at)
        .limit(limit)
        .all()
    )

    return messages
