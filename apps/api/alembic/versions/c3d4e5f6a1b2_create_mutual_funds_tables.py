"""create mutual funds tables

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-11-16 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a1b2'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. mutual_funds table
    op.create_table(
        'mutual_funds',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('scheme_code', sa.String(length=50), nullable=False),
        sa.Column('isin', sa.String(length=20), nullable=True),
        sa.Column('scheme_name', sa.String(length=255), nullable=False),
        sa.Column('amc_name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('subcategory', sa.String(length=100), nullable=False),
        sa.Column('plan_type', sa.String(length=20), nullable=False, server_default='Direct'),
        sa.Column('option_type', sa.String(length=20), nullable=False, server_default='Growth'),
        sa.Column('benchmark_name', sa.String(length=150), nullable=True),
        sa.Column('expense_ratio', sa.Numeric(precision=6, scale=4), nullable=True),
        sa.Column('aum_crores', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('fund_manager', sa.String(length=200), nullable=True),
        sa.Column('crisil_rating', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('scheme_code', name='uq_mutual_funds_scheme_code'),
    )
    op.create_index(op.f('ix_mutual_funds_scheme_code'), 'mutual_funds', ['scheme_code'], unique=True)
    op.create_index(op.f('ix_mutual_funds_isin'), 'mutual_funds', ['isin'], unique=False)
    op.create_index(op.f('ix_mutual_funds_scheme_name'), 'mutual_funds', ['scheme_name'], unique=False)
    op.create_index(op.f('ix_mutual_funds_amc_name'), 'mutual_funds', ['amc_name'], unique=False)
    op.create_index(op.f('ix_mutual_funds_category'), 'mutual_funds', ['category'], unique=False)
    op.create_index(op.f('ix_mutual_funds_subcategory'), 'mutual_funds', ['subcategory'], unique=False)
    op.create_index('ix_mutual_funds_cat_subcat', 'mutual_funds', ['category', 'subcategory'], unique=False)

    # 2. fund_nav_history table
    op.create_table(
        'fund_nav_history',
        sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
        sa.Column('fund_id', sa.Uuid(), nullable=False),
        sa.Column('nav_date', sa.Date(), nullable=False),
        sa.Column('nav', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('repurchase_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('sale_price', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('nav > 0', name='ck_fund_nav_positive'),
        sa.ForeignKeyConstraint(['fund_id'], ['mutual_funds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('fund_id', 'nav_date', name='uq_fund_nav_fund_date'),
    )
    op.create_index(op.f('ix_fund_nav_history_fund_id'), 'fund_nav_history', ['fund_id'], unique=False)
    op.create_index(op.f('ix_fund_nav_history_nav_date'), 'fund_nav_history', ['nav_date'], unique=False)
    op.create_index('ix_fund_nav_fund_date', 'fund_nav_history', ['fund_id', 'nav_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_fund_nav_fund_date', table_name='fund_nav_history')
    op.drop_index(op.f('ix_fund_nav_history_nav_date'), table_name='fund_nav_history')
    op.drop_index(op.f('ix_fund_nav_history_fund_id'), table_name='fund_nav_history')
    op.drop_table('fund_nav_history')

    op.drop_index('ix_mutual_funds_cat_subcat', table_name='mutual_funds')
    op.drop_index(op.f('ix_mutual_funds_subcategory'), table_name='mutual_funds')
    op.drop_index(op.f('ix_mutual_funds_category'), table_name='mutual_funds')
    op.drop_index(op.f('ix_mutual_funds_amc_name'), table_name='mutual_funds')
    op.drop_index(op.f('ix_mutual_funds_scheme_name'), table_name='mutual_funds')
    op.drop_index(op.f('ix_mutual_funds_isin'), table_name='mutual_funds')
    op.drop_index(op.f('ix_mutual_funds_scheme_code'), table_name='mutual_funds')
    op.drop_table('mutual_funds')
