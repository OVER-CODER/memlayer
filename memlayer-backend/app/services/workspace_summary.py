"""
Workspace Summary Service - Manages persistent, evolving workspace summaries.

This service periodically updates high-level summaries of workspace state,
which acts as persistent cognition about the workspace's direction and key topics.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.db.models import WorkspaceSummary, Memory, Message, Chat, Workspace
from app.services.embedding import get_embedding_service
from app.services.llm import get_llm_service
from app.services.providers import GenerationConfig
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)


class WorkspaceSummaryService:
    """Manages workspace summaries.

    This service:
    - Periodically updates workspace summaries based on recent activity
    - Extracts key topics and emerging patterns
    - Maintains persistent high-level workspace cognition
    - Tracks summary lineage and generation metadata
    """

    def __init__(self, db: Session):
        """Initialize summary service.

        Args:
            db: Database session
        """
        self.db = db
        self.embedding_service = get_embedding_service()
        self.llm_service = get_llm_service()

        # Configuration
        self.summary_update_interval = timedelta(hours=1)  # Update summaries hourly
        self.summary_min_messages_threshold = 5  # Minimum messages before summary
        self.summary_max_memory_context = 10  # Max memories to consider

    def maybe_update_summary(
        self,
        workspace_id: str,
        force: bool = False,
    ) -> Optional[WorkspaceSummary]:
        """Conditionally update workspace summary.

        Updates only if:
        - force=True, or
        - Enough time has passed since last update, or
        - Enough new messages/memories since last update

        Args:
            workspace_id: ID of workspace
            force: Force update regardless of conditions

        Returns:
            Updated WorkspaceSummary or None if no update
        """
        # Get or create summary record
        summary_record = (
            self.db.query(WorkspaceSummary)
            .filter(WorkspaceSummary.workspace_id == workspace_id)
            .first()
        )

        if not summary_record:
            logger.info(f"Creating first summary for workspace {workspace_id}")
            return self._create_initial_summary(workspace_id)

        # Check if update is needed
        time_since_last_update = datetime.now(timezone.utc) - summary_record.updated_at
        recent_messages = self._count_recent_messages(
            workspace_id,
            since=summary_record.updated_at,
        )
        recent_memories = self._count_recent_memories(
            workspace_id,
            since=summary_record.updated_at,
        )

        should_update = (
            force
            or time_since_last_update >= self.summary_update_interval
            or (recent_messages + recent_memories)
            >= self.summary_min_messages_threshold
        )

        if not should_update:
            logger.debug(
                f"Summary update not needed for workspace {workspace_id} - "
                f"Time since last: {time_since_last_update.total_seconds()}s, "
                f"Recent activity: {recent_messages} messages, {recent_memories} memories"
            )
            return None

        logger.info(f"Updating summary for workspace {workspace_id}")
        return self._update_summary(workspace_id, summary_record)

    def _create_initial_summary(self, workspace_id: str) -> WorkspaceSummary:
        """Create the first summary for a workspace."""
        workspace = (
            self.db.query(Workspace).filter(Workspace.id == workspace_id).first()
        )

        if not workspace:
            raise ValueError(f"Workspace {workspace_id} not found")

        # Initial summary is just workspace metadata
        summary_text = f"New workspace: {workspace.name}"
        if workspace.description:
            summary_text += f"\n{workspace.description}"

        summary = WorkspaceSummary(
            workspace_id=workspace_id,
            summary_text=summary_text,
            summary_embedding=self.embedding_service.embed(summary_text),
            total_messages=0,
            total_memories=0,
            key_topics=[],
            generated_from_message_count=0,
            last_summary_trigger_reason="initial_creation",
        )

        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)

        logger.info(f"Created initial summary for workspace {workspace_id}")
        return summary

    def _update_summary(
        self,
        workspace_id: str,
        current_summary: WorkspaceSummary,
    ) -> WorkspaceSummary:
        """Update an existing workspace summary."""

        # Get recent memories
        recent_memories = self._get_recent_memories(
            workspace_id, limit=self.summary_max_memory_context
        )

        # Extract key topics from memories
        key_topics = self._extract_key_topics(recent_memories)

        # Get workspace statistics
        total_messages = self._count_total_messages(workspace_id)
        total_memories = self._count_total_memories(workspace_id)
        recent_messages_count = self._count_recent_messages(
            workspace_id,
            since=current_summary.updated_at,
        )

        # Generate new summary using LLM
        new_summary_text = self._generate_summary_text(
            workspace_id,
            recent_memories,
            key_topics,
            current_summary.summary_text,
        )

        # Update record
        current_summary.summary_text = new_summary_text
        current_summary.summary_embedding = self.embedding_service.embed(
            new_summary_text
        )
        current_summary.total_messages = total_messages
        current_summary.total_memories = total_memories
        current_summary.key_topics = key_topics
        current_summary.generated_from_message_count = recent_messages_count
        current_summary.last_summary_trigger_reason = "periodic_update"
        current_summary.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(current_summary)

        logger.info(
            f"Updated summary for workspace {workspace_id} - "
            f"Topics: {', '.join(key_topics)}, "
            f"Messages: {total_messages}, "
            f"Memories: {total_memories}"
        )

        return current_summary

    def _generate_summary_text(
        self,
        workspace_id: str,
        memories: List[Memory],
        topics: List[str],
        previous_summary: Optional[str],
    ) -> str:
        """Generate summary text using LLM.

        Args:
            workspace_id: Workspace ID
            memories: Recent memories to summarize
            topics: Extracted topics
            previous_summary: Previous summary for continuity

        Returns:
            Generated summary text
        """
        # Build context for LLM
        memory_context = "\n".join(
            [f"- {m.summary or m.raw_content[:100]}" for m in memories]
        )

        topics_str = ", ".join(topics) if topics else "No clear topics yet"

        prompt = f"""Summarize the current state of this workspace concisely.

Previous Summary:
{previous_summary or "No previous summary"}

Recent Topics:
{topics_str}

Recent Memories:
{memory_context}

Provide a 2-3 sentence summary that captures:
1. The main focus/direction of the workspace
2. Key patterns or themes
3. Current state of understanding

Summary:"""

        try:
            config = GenerationConfig(
                temperature=0.5,
                max_tokens=256,
            )

            result = self.llm_service.generate(prompt, config)
            return result.text.strip()

        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fall back to simple summary
            return (
                f"Workspace with {len(memories)} recent items on topics: {topics_str}"
            )

    def _extract_key_topics(self, memories: List[Memory]) -> List[str]:
        """Extract key topics from memories.

        This is a simple implementation that extracts high-importance topics.
        Could be enhanced with NLP techniques.

        Args:
            memories: List of memories

        Returns:
            List of topic strings
        """
        if not memories:
            return []

        # Simple approach: extract from memory summaries
        topics = set()

        for memory in memories:
            if memory.extra_metadata and "topic" in memory.extra_metadata:
                topic = memory.extra_metadata["topic"]
                if isinstance(topic, (list, tuple)):
                    topics.update(topic)
                else:
                    topics.add(str(topic))

        # If no explicit topics, use first few words from summaries
        if not topics:
            for memory in memories[:3]:  # Limit to top 3 memories
                summary = memory.summary or memory.raw_content
                # Extract first meaningful phrase
                words = summary.split()[:3]
                if words:
                    topics.add(" ".join(words))

        return list(topics)[:5]  # Limit to top 5 topics

    def _get_recent_memories(
        self,
        workspace_id: str,
        since: Optional[datetime] = None,
        limit: int = 10,
    ) -> List[Memory]:
        """Get recent memories from workspace.

        Args:
            workspace_id: Workspace ID
            since: Only memories after this timestamp
            limit: Maximum memories to return

        Returns:
            List of Memory objects
        """
        query = self.db.query(Memory).filter(Memory.workspace_id == workspace_id)

        if since:
            query = query.filter(Memory.timestamp >= since)

        return query.order_by(desc(Memory.importance_score)).limit(limit).all()

    def _count_recent_messages(
        self,
        workspace_id: str,
        since: Optional[datetime] = None,
    ) -> int:
        """Count recent messages in workspace.

        Args:
            workspace_id: Workspace ID
            since: Only count messages after this timestamp

        Returns:
            Count of messages
        """
        query = self.db.query(Message)

        # Join through Chat to Workspace
        chats = self.db.query(Chat).filter(Chat.workspace_id == workspace_id).all()

        chat_ids = [c.id for c in chats]

        if not chat_ids:
            return 0

        query = query.filter(Message.chat_id.in_(chat_ids))

        if since:
            query = query.filter(Message.created_at >= since)

        return query.count()

    def _count_total_messages(self, workspace_id: str) -> int:
        """Count total messages in workspace."""
        chats = self.db.query(Chat).filter(Chat.workspace_id == workspace_id).all()

        if not chats:
            return 0

        chat_ids = [c.id for c in chats]
        return self.db.query(Message).filter(Message.chat_id.in_(chat_ids)).count()

    def _count_recent_memories(
        self,
        workspace_id: str,
        since: datetime,
    ) -> int:
        """Count memories created since timestamp."""
        return (
            self.db.query(Memory)
            .filter(
                Memory.workspace_id == workspace_id,
                Memory.timestamp >= since,
            )
            .count()
        )

    def _count_total_memories(self, workspace_id: str) -> int:
        """Count total memories in workspace."""
        return self.db.query(Memory).filter(Memory.workspace_id == workspace_id).count()

    def get_summary(self, workspace_id: str) -> Optional[WorkspaceSummary]:
        """Get current summary for workspace.

        Args:
            workspace_id: Workspace ID

        Returns:
            WorkspaceSummary or None
        """
        return (
            self.db.query(WorkspaceSummary)
            .filter(WorkspaceSummary.workspace_id == workspace_id)
            .first()
        )

    def get_summary_dict(self, workspace_id: str) -> Optional[Dict]:
        """Get summary as dictionary.

        Args:
            workspace_id: Workspace ID

        Returns:
            Dictionary representation of summary
        """
        summary = self.get_summary(workspace_id)
        if not summary:
            return None

        return {
            "id": summary.id,
            "workspace_id": summary.workspace_id,
            "summary": summary.summary_text,
            "key_topics": summary.key_topics,
            "total_messages": summary.total_messages,
            "total_memories": summary.total_memories,
            "updated_at": summary.updated_at.isoformat(),
            "created_at": summary.created_at.isoformat(),
        }
