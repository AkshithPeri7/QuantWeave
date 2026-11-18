"""create ai tables

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-11-16 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a1b2c3d4e5'
down_revision: Union[str, Sequence[str], None] = 'e5f6a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. ai_conversations
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=150), server_default='Financial Research', nullable=False),
        sa.Column('context_module', sa.String(length=50), nullable=True),
        sa.Column('context_entity_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_conversations_user_id'), 'ai_conversations', ['user_id'], unique=False)

    # 2. ai_messages
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('conversation_id', sa.Uuid(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('provider', sa.String(length=50), server_default='mock', nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='COMPLETED', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['ai_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_messages_conversation_id'), 'ai_messages', ['conversation_id'], unique=False)

    # 3. ai_tool_executions
    op.create_table(
        'ai_tool_executions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('message_id', sa.Uuid(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('arguments', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='SUCCESS', nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['ai_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_tool_executions_message_id'), 'ai_tool_executions', ['message_id'], unique=False)
    op.create_index(op.f('ix_ai_tool_executions_tool_name'), 'ai_tool_executions', ['tool_name'], unique=False)

    # 4. ai_retrieval_sources
    op.create_table(
        'ai_retrieval_sources',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('message_id', sa.Uuid(), nullable=False),
        sa.Column('source_title', sa.String(length=200), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('citation_key', sa.String(length=50), nullable=False),
        sa.Column('snippet', sa.Text(), nullable=False),
        sa.Column('relevance_score', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['message_id'], ['ai_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_retrieval_sources_message_id'), 'ai_retrieval_sources', ['message_id'], unique=False)

    # 5. ai_evaluation_runs
    op.create_table(
        'ai_evaluation_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('evaluation_name', sa.String(length=150), nullable=False),
        sa.Column('total_cases', sa.Integer(), nullable=False),
        sa.Column('passed_cases', sa.Integer(), nullable=False),
        sa.Column('accuracy_pct', sa.Float(), nullable=False),
        sa.Column('results_summary', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('ai_evaluation_runs')

    op.drop_index(op.f('ix_ai_retrieval_sources_message_id'), table_name='ai_retrieval_sources')
    op.drop_table('ai_retrieval_sources')

    op.drop_index(op.f('ix_ai_tool_executions_tool_name'), table_name='ai_tool_executions')
    op.drop_index(op.f('ix_ai_tool_executions_message_id'), table_name='ai_tool_executions')
    op.drop_table('ai_tool_executions')

    op.drop_index(op.f('ix_ai_messages_conversation_id'), table_name='ai_messages')
    op.drop_table('ai_messages')

    op.drop_index(op.f('ix_ai_conversations_user_id'), table_name='ai_conversations')
    op.drop_table('ai_conversations')
