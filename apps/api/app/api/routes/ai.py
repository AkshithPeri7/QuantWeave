"""
QuantWeave AI Copilot API Routes.

Implements:
- AI Conversation session creation, retrieval, listing, and deletion
- User message dispatch through AIOrchestrator with RAG grounding and read-only tool invocation
- Available tools catalog inspection
- Automated benchmark evaluation runner
"""

from typing import Any, Dict, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.evaluation import run_ai_evaluation_suite
from app.ai.orchestrator import AIOrchestrator
from app.ai.tools import AVAILABLE_TOOLS
from app.api.deps import get_current_user, get_db
from app.core.rate_limiter import limit_ai_chat
from app.models.ai import AIConversation, AIMessage
from app.models.user import User
from app.schemas.ai import (
    ChatTurnResponse,
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    EvaluationResponse,
    SendMessageRequest,
    ToolCatalogItem,
)

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new AI research conversation for the authenticated user.
    """
    conv = AIOrchestrator.get_or_create_conversation(
        db=db,
        user=current_user,
        title=payload.title,
        context_module=payload.context_module,
        context_entity_id=payload.context_entity_id,
    )
    return conv


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all AI conversations belonging to the authenticated user.
    """
    conversations = (
        db.query(AIConversation)
        .filter(AIConversation.user_id == current_user.id)
        .order_by(AIConversation.updated_at.desc())
        .all()
    )
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a conversation by ID, along with its full message history, tool executions, and citations.
    """
    conv = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id, AIConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )
    return conv


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes an AI conversation and cascades deletion to all messages, tool executions, and retrieval sources.
    """
    conv = (
        db.query(AIConversation)
        .filter(AIConversation.id == conversation_id, AIConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found or access denied.",
        )
    db.delete(conv)
    db.commit()
    return None


@router.post("/conversations/{conversation_id}/messages", response_model=ChatTurnResponse)
def send_message(
    conversation_id: uuid.UUID,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _limit: None = Depends(limit_ai_chat),
):
    """
    Sends a user prompt to the Copilot. The system performs:
    1. Context retrieval and RAG knowledge search
    2. Tool routing and deterministic execution
    3. LLM generation with mandatory educational disclaimers
    4. Full message, execution, and provenance persistence
    """
    try:
        turn_result = AIOrchestrator.process_user_turn(
            db=db,
            user=current_user,
            conversation_id=conversation_id,
            user_prompt=payload.content,
            context_module=payload.context_module,
            context_entity_id=payload.context_entity_id,
        )
        return turn_result
    except PermissionError as pe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(pe),
        )
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing AI research turn: {str(e)}",
        )


@router.get("/tools", response_model=List[ToolCatalogItem])
def list_available_tools(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the catalog of all available server-side read-only financial tools.
    """
    catalog = []
    for name, tool_spec in AVAILABLE_TOOLS.items():
        catalog.append(
            ToolCatalogItem(
                name=name,
                description=tool_spec.get("description", ""),
                parameters=tool_spec.get("parameters", {}),
            )
        )
    return catalog


@router.post("/evaluate", response_model=EvaluationResponse)
def run_evaluation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executes the automated benchmark evaluation suite verifying factual correctness,
    tool invocation accuracy, and security guardrail compliance.
    """
    res = run_ai_evaluation_suite(db=db, eval_user=current_user)
    return res
