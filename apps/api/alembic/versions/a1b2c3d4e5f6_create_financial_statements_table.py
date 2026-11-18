"""create financial statements table

Revision ID: a1b2c3d4e5f6
Revises: 35b3591b794d
Create Date: 2026-11-16 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '35b3591b794d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'financial_statements',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('instrument_id', sa.Uuid(), nullable=False),
        sa.Column('provider_id', sa.Uuid(), nullable=True),
        sa.Column('statement_type', sa.String(length=30), nullable=False, server_default='annual_consolidated'),
        sa.Column('period_type', sa.String(length=20), nullable=False, server_default='annual'),
        sa.Column('fiscal_year', sa.Integer(), nullable=False),
        sa.Column('fiscal_quarter', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('period_start_date', sa.Date(), nullable=True),
        sa.Column('period_end_date', sa.Date(), nullable=False),
        sa.Column('filing_date', sa.Date(), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default=sa.true()),
        # Income statement
        sa.Column('revenue', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('cost_of_goods_sold', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('gross_profit', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('operating_expenses', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('operating_income', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('interest_expense', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('tax_expense', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('net_income', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('diluted_shares', sa.Numeric(precision=20, scale=2), nullable=True),
        sa.Column('eps', sa.Numeric(precision=14, scale=4), nullable=True),
        # Balance sheet
        sa.Column('cash_and_equivalents', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_current_assets', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_non_current_assets', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_assets', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_current_liabilities', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_long_term_debt', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_debt', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('total_liabilities', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('shareholder_equity', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('book_value_per_share', sa.Numeric(precision=14, scale=4), nullable=True),
        # Cash flow
        sa.Column('operating_cash_flow', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('capital_expenditures', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('free_cash_flow', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('investing_cash_flow', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('financing_cash_flow', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('net_change_in_cash', sa.Numeric(precision=24, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['provider_id'], ['data_sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'instrument_id',
            'period_type',
            'fiscal_year',
            'fiscal_quarter',
            name='uq_financial_statement_period',
        )
    )
    op.create_index(
        op.f('ix_financial_statements_instrument_id'),
        'financial_statements',
        ['instrument_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_financial_statements_fiscal_year'),
        'financial_statements',
        ['fiscal_year'],
        unique=False,
    )
    op.create_index(
        op.f('ix_financial_statements_period_end_date'),
        'financial_statements',
        ['period_end_date'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_financial_statements_period_end_date'), table_name='financial_statements')
    op.drop_index(op.f('ix_financial_statements_fiscal_year'), table_name='financial_statements')
    op.drop_index(op.f('ix_financial_statements_instrument_id'), table_name='financial_statements')
    op.drop_table('financial_statements')
