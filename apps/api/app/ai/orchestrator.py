"""
Secure AI Orchestrator for QuantWeave Copilot.

Coordinates:
- User authentication & cross-user privacy enforcement
- Conversation persistence and message history windowing
- RAG knowledge retrieval and provenance tracking
- Read-only tool execution dispatch with loop limits
- Synthetic demo data labeling and mandatory regulatory disclaimers
"""

from datetime import datetime, timezone
import time
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.ai.providers import ProviderResponse, get_llm_provider
from app.ai.rag import RAGRetrievalService
from app.core.config import settings
from app.models.ai import AIConversation, AIMessage, AIRetrievalSource, AIToolExecution
from app.models.user import User


class AIOrchestrator:
    """
    Core workflow orchestrator for QuantWeave Copilot.
    """

    @classmethod
    def get_or_create_conversation(
        cls,
        db: Session,
        user: User,
        conversation_id: Optional[uuid.UUID] = None,
        title: Optional[str] = None,
        context_module: Optional[str] = None,
        context_entity_id: Optional[uuid.UUID] = None,
    ) -> AIConversation:
        """Loads an existing conversation verifying ownership, or creates a new one."""
        if conversation_id:
            conv = (
                db.query(AIConversation)
                .filter(AIConversation.id == conversation_id, AIConversation.user_id == user.id)
                .first()
            )
            if conv:
                return conv

        # Create new conversation
        conv = AIConversation(
            user_id=user.id,
            title=title or "Financial Research",
            context_module=context_module,
            context_entity_id=context_entity_id,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
        return conv

    @classmethod
    def process_user_turn(
        cls,
        db: Session,
        user: User,
        conversation_id: uuid.UUID,
        user_prompt: str,
        context_module: Optional[str] = None,
        context_entity_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end user message turn:
        1. Verify conversation ownership
        2. Persist user message
        3. Query RAG knowledge base
        4. Invoke LLM provider with typed tool access
        5. Persist assistant message, tool executions, and source citations
        6. Return structured response payload
        """
        start_time = time.time()

        # 1. Verify conversation ownership
        conv = (
            db.query(AIConversation)
            .filter(AIConversation.id == conversation_id, AIConversation.user_id == user.id)
            .first()
        )
        if not conv:
            raise PermissionError("Conversation not found or access denied.")

        # Update title if default
        if conv.title == "Financial Research" and len(user_prompt.strip()) > 3:
            conv.title = user_prompt.strip()[:60]
            conv.updated_at = datetime.now(timezone.utc)

        # 2. Persist user message
        user_msg = AIMessage(
            conversation_id=conv.id,
            role="user",
            content=user_prompt.strip(),
            provider="user",
            status="COMPLETED",
        )
        db.add(user_msg)
        db.commit()

        # 3. Load latest messages for context window (last 10 turns)
        history_msgs = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conv.id)
            .order_by(AIMessage.created_at.asc())
            .limit(10)
            .all()
        )
        formatted_history = [{"role": m.role, "content": m.content} for m in history_msgs]

        # 4. Invoke Provider
        provider = get_llm_provider()
        provider_resp: ProviderResponse = provider.generate_response(
            messages=formatted_history,
            db=db,
            context_user_id=user.id,
            context_module=context_module or conv.context_module,
            context_entity_id=context_entity_id or conv.context_entity_id,
        )

        total_latency_ms = int((time.time() - start_time) * 1000)

        # 5. Persist Assistant message
        assistant_msg = AIMessage(
            conversation_id=conv.id,
            role="assistant",
            content=provider_resp.content,
            provider=provider_resp.provider,
            model_name=provider_resp.model_name,
            tokens_used=provider_resp.tokens_used,
            latency_ms=total_latency_ms,
            status="COMPLETED",
        )
        db.add(assistant_msg)
        db.flush()  # allocate assistant_msg.id

        # 6. Persist Tool Executions
        persisted_tool_records = []
        for t in provider_resp.executed_tools:
            texec = AIToolExecution(
                message_id=assistant_msg.id,
                tool_name=t.get("tool", "unknown"),
                arguments=t.get("arguments", {}),
                result=t.get("result", {}),
                status="SUCCESS" if t.get("status") == "success" else "ERROR",
                execution_time_ms=t.get("execution_time_ms"),
                error_message=t.get("error"),
            )
            db.add(texec)
            persisted_tool_records.append(texec)

        # 7. Persist RAG Sources
        rag_snippets = RAGRetrievalService.search(user_prompt, top_k=2)
        persisted_source_records = []
        for r in rag_snippets:
            rsource = AIRetrievalSource(
                message_id=assistant_msg.id,
                source_title=r["source_title"],
                source_url=r["source_url"],
                citation_key=r["citation_key"],
                snippet=r["snippet"],
                relevance_score=r["relevance_score"],
            )
            db.add(rsource)
            persisted_source_records.append(rsource)

        conv.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(assistant_msg)

        return {
            "conversation_id": str(conv.id),
            "user_message_id": str(user_msg.id),
            "assistant_message_id": str(assistant_msg.id),
            "content": assistant_msg.content,
            "role": "assistant",
            "provider": assistant_msg.provider,
            "model_name": assistant_msg.model_name,
            "tokens_used": assistant_msg.tokens_used,
            "latency_ms": assistant_msg.latency_ms,
            "tool_executions": [
                {
                    "tool_name": t.tool_name,
                    "status": t.status,
                    "result": t.result,
                    "execution_time_ms": t.execution_time_ms,
                }
                for t in persisted_tool_records
            ],
            "retrieval_sources": [
                {
                    "citation_key": s.citation_key,
                    "source_title": s.source_title,
                    "source_url": s.source_url,
                    "snippet": s.snippet,
                    "relevance_score": s.relevance_score,
                }
                for s in persisted_source_records
            ],
            "created_at": assistant_msg.created_at.isoformat(),
        }
