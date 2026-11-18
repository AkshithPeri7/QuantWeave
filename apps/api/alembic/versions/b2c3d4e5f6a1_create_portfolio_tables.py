"""create portfolio tables

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-11-16 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_portfolios_user_id'), 'portfolios', ['user_id'], unique=False)

    # 2. portfolio_transactions table
    op.create_table(
        'portfolio_transactions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('portfolio_id', sa.Uuid(), nullable=False),
        sa.Column('instrument_id', sa.Uuid(), nullable=True),
        sa.Column('transaction_type', sa.String(length=30), nullable=False),
        sa.Column('trade_date', sa.Date(), nullable=False),
        sa.Column('trade_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=24, scale=8), nullable=False, server_default='0'),
        sa.Column('price_per_unit', sa.Numeric(precision=20, scale=6), nullable=False, server_default='0'),
        sa.Column('fees', sa.Numeric(precision=20, scale=6), nullable=False, server_default='0'),
        sa.Column('cash_amount', sa.Numeric(precision=20, scale=6), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(length=120), nullable=True),
        sa.Column('reversed_transaction_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('quantity >= 0', name='chk_portfolio_tx_quantity_non_negative'),
        sa.CheckConstraint('price_per_unit >= 0', name='chk_portfolio_tx_price_non_negative'),
        sa.CheckConstraint('fees >= 0', name='chk_portfolio_tx_fees_non_negative'),
        sa.ForeignKeyConstraint(['portfolio_id'], ['portfolios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reversed_transaction_id'], ['portfolio_transactions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_portfolio_tx_idempotency_key'),
    )
    op.create_index(op.f('ix_portfolio_transactions_portfolio_id'), 'portfolio_transactions', ['portfolio_id'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_instrument_id'), 'portfolio_transactions', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_trade_date'), 'portfolio_transactions', ['trade_date'], unique=False)
    op.create_index(op.f('ix_portfolio_transactions_idempotency_key'), 'portfolio_transactions', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_portfolio_transactions_idempotency_key'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_trade_date'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_instrument_id'), table_name='portfolio_transactions')
    op.drop_index(op.f('ix_portfolio_transactions_portfolio_id'), table_name='portfolio_transactions')
    op.drop_table('portfolio_transactions')

    op.drop_index(op.f('ix_portfolios_user_id'), table_name='portfolios')
    op.drop_table('portfolios')
