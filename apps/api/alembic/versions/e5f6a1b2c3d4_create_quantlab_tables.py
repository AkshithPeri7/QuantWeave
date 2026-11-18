"""create quantlab tables

Revision ID: e5f6a1b2c3d4
Revises: d4e5f6a1b2c3
Create Date: 2026-11-16 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. research_strategies
    op.create_table(
        'research_strategies',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_type', sa.String(length=50), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_strategies_user_id'), 'research_strategies', ['user_id'], unique=False)
    op.create_index(op.f('ix_research_strategies_strategy_type'), 'research_strategies', ['strategy_type'], unique=False)

    # 2. backtest_runs
    op.create_table(
        'backtest_runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('strategy_id', sa.Uuid(), nullable=True),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('instrument_id', sa.Uuid(), nullable=False),
        sa.Column('starting_capital', sa.Numeric(precision=15, scale=2), server_default='100000.00', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('fee_rate', sa.Float(), server_default='0.001', nullable=False),
        sa.Column('slippage_bps', sa.Float(), server_default='5.0', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='COMPLETED', nullable=False),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('dataset_fingerprint', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['research_strategies.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backtest_runs_strategy_id'), 'backtest_runs', ['strategy_id'], unique=False)
    op.create_index(op.f('ix_backtest_runs_user_id'), 'backtest_runs', ['user_id'], unique=False)
    op.create_index(op.f('ix_backtest_runs_instrument_id'), 'backtest_runs', ['instrument_id'], unique=False)
    op.create_index(op.f('ix_backtest_runs_status'), 'backtest_runs', ['status'], unique=False)

    # 3. backtest_trades
    op.create_table(
        'backtest_trades',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('signal_date', sa.Date(), nullable=False),
        sa.Column('execution_date', sa.Date(), nullable=False),
        sa.Column('quantity', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('execution_price', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('fees', sa.Numeric(precision=15, scale=4), server_default='0.0000', nullable=False),
        sa.Column('slippage_cost', sa.Numeric(precision=15, scale=4), server_default='0.0000', nullable=False),
        sa.Column('cash_after', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('position_after', sa.Numeric(precision=15, scale=4), nullable=False),
        sa.Column('realized_pnl', sa.Numeric(precision=15, scale=4), nullable=True),
        sa.Column('pnl_pct', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['backtest_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backtest_trades_run_id'), 'backtest_trades', ['run_id'], unique=False)

    # 4. backtest_equity_points
    op.create_table(
        'backtest_equity_points',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('run_id', sa.Uuid(), nullable=False),
        sa.Column('point_date', sa.Date(), nullable=False),
        sa.Column('equity', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('cash', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('position_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('drawdown_pct', sa.Numeric(precision=8, scale=4), nullable=False),
        sa.Column('benchmark_equity', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['run_id'], ['backtest_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('run_id', 'point_date', name='uq_backtest_equity_point')
    )
    op.create_index(op.f('ix_backtest_equity_points_run_id'), 'backtest_equity_points', ['run_id'], unique=False)
    op.create_index('ix_backtest_equity_run_date', 'backtest_equity_points', ['run_id', 'point_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_backtest_equity_run_date', table_name='backtest_equity_points')
    op.drop_index(op.f('ix_backtest_equity_points_run_id'), table_name='backtest_equity_points')
    op.drop_table('backtest_equity_points')

    op.drop_index(op.f('ix_backtest_trades_run_id'), table_name='backtest_trades')
    op.drop_table('backtest_trades')

    op.drop_index(op.f('ix_backtest_runs_status'), table_name='backtest_runs')
    op.drop_index(op.f('ix_backtest_runs_instrument_id'), table_name='backtest_runs')
    op.drop_index(op.f('ix_backtest_runs_user_id'), table_name='backtest_runs')
    op.drop_index(op.f('ix_backtest_runs_strategy_id'), table_name='backtest_runs')
    op.drop_table('backtest_runs')

    op.drop_index(op.f('ix_research_strategies_strategy_type'), table_name='research_strategies')
    op.drop_index(op.f('ix_research_strategies_user_id'), table_name='research_strategies')
    op.drop_table('research_strategies')
