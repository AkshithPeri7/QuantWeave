"""
SQLAlchemy models for QuantWeave AI Financial Copilot & Intelligent Research.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class AIConversation(Base):
    """
    User-owned conversation thread with QuantWeave Copilot.
    """
    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Financial Research",
    )
    context_module: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # 'equity', 'portfolio', 'funds', 'market', 'quantlab'
    context_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    messages: Mapped[List["AIMessage"]] = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at.asc()",
    )


class AIMessage(Base):
    """
    Individual chat turn (user, assistant, or system) within a conversation.
    """
    __tablename__ = "ai_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # 'user', 'assistant', 'system'
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    provider: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="mock",
    )
    model_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    tokens_used: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        default=0,
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="COMPLETED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    conversation: Mapped["AIConversation"] = relationship(
        "AIConversation",
        back_populates="messages",
    )
    tool_executions: Mapped[List["AIToolExecution"]] = relationship(
        "AIToolExecution",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="AIToolExecution.created_at.asc()",
    )
    retrieval_sources: Mapped[List["AIRetrievalSource"]] = relationship(
        "AIRetrievalSource",
        back_populates="message",
        cascade="all, delete-orphan",
        order_by="AIRetrievalSource.created_at.asc()",
    )


class AIToolExecution(Base):
    """
    Audit record of a server-side read-only tool invocation executed during an assistant turn.
    """
    __tablename__ = "ai_tool_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    arguments: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    result: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SUCCESS",
    )  # 'SUCCESS', 'ERROR', 'DENIED'
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    message: Mapped["AIMessage"] = relationship(
        "AIMessage",
        back_populates="tool_executions",
    )


class AIRetrievalSource(Base):
    """
    Transparent citation and provenance reference retrieved from the RAG knowledge base.
    """
    __tablename__ = "ai_retrieval_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    message_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    citation_key: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g. '[DOC-01]'
    snippet: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    message: Mapped["AIMessage"] = relationship(
        "AIMessage",
        back_populates="retrieval_sources",
    )


class AIEvaluationRun(Base):
    """
    Automated benchmark evaluation run tracking factual accuracy, tool selection, and refusal rates.
    """
    __tablename__ = "ai_evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    evaluation_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )
    total_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    passed_cases: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    accuracy_pct: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    results_summary: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
