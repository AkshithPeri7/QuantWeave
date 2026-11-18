"""
Pydantic Schemas for QuantWeave AI Financial Copilot.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=150, description="Optional custom conversation title")
    context_module: Optional[str] = Field(default=None, description="Initial module context ('equity', 'portfolio', etc.)")
    context_entity_id: Optional[uuid.UUID] = Field(default=None, description="Initial entity ID (stock UUID or portfolio UUID)")


class ConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    context_module: Optional[str] = None
    context_entity_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    messages: List["MessageResponse"] = Field(default_factory=list)


class ToolExecutionResponse(BaseModel):
    tool_name: str
    status: str
    result: Dict[str, Any]
    execution_time_ms: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class RetrievalSourceResponse(BaseModel):
    citation_key: str
    source_title: str
    source_url: Optional[str] = None
    snippet: str
    relevance_score: float

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
    created_at: datetime
    tool_executions: List[ToolExecutionResponse] = Field(default_factory=list)
    retrieval_sources: List[RetrievalSourceResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000, description="User prompt or research query")
    context_module: Optional[str] = Field(default=None, description="Current module ('equity', 'portfolio', 'funds', etc.)")
    context_entity_id: Optional[uuid.UUID] = Field(default=None, description="Active entity ID for contextual grounding")


class ChatTurnResponse(BaseModel):
    conversation_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    content: str
    role: str = "assistant"
    provider: str
    model_name: str
    tokens_used: int
    latency_ms: int
    tool_executions: List[ToolExecutionResponse]
    retrieval_sources: List[RetrievalSourceResponse]
    created_at: str


class ToolCatalogItem(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class EvaluationResponse(BaseModel):
    evaluation_id: uuid.UUID
    total_cases: int
    passed_cases: int
    accuracy_pct: float
    results: List[Dict[str, Any]]
