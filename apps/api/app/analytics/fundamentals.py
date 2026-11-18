"""
Fundamental Analysis and Financial Ratio Engine for QuantWeave.

Calculates standard corporate financial ratios with explicit edge-case protections:
- Gross Margin, Operating Margin, Net Profit Margin
- Return on Equity (ROE)
- Debt-to-Equity (D/E)
- Current Ratio
- Price-to-Earnings (P/E)
- Price-to-Book (P/B)

Division-by-zero guards:
- If revenue == 0: margins return None
- If shareholder_equity <= 0: ROE and D/E return None
- If current_liabilities <= 0: Current Ratio returns None
- If eps <= 0: P/E returns None (loss-making companies have undefined P/E)
- If book_value_per_share <= 0: P/B returns None
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.models.financial_statement import FinancialStatement


@dataclass
class FundamentalRatios:
    period_type: str  # "annual" or "quarterly"
    fiscal_year: int
    fiscal_quarter: Optional[int]
    period_end_date: str
    currency: str
    is_synthetic: bool
    # Valuation (requires latest price)
    price: Optional[float]
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    # Profitability Margins (%)
    gross_margin_pct: Optional[float]
    operating_margin_pct: Optional[float]
    net_margin_pct: Optional[float]
    roe_pct: Optional[float]
    # Leverage & Liquidity
    debt_to_equity: Optional[float]
    current_ratio: Optional[float]
    # Raw items in Crore / Millions
    revenue: Optional[float]
    net_income: Optional[float]
    operating_income: Optional[float]
    eps: Optional[float]
    total_assets: Optional[float]
    total_debt: Optional[float]
    shareholder_equity: Optional[float]
    operating_cash_flow: Optional[float]
    free_cash_flow: Optional[float]


def calculate_statement_ratios(
    statement: FinancialStatement,
    latest_price: Optional[float] = None,
) -> FundamentalRatios:
    """
    Computes all fundamental valuation and profitability ratios for a given financial statement.
    """
    def to_float(val: Any) -> Optional[float]:
        if val is None:
            return None
        return float(val)

    rev = to_float(statement.revenue)
    gp = to_float(statement.gross_profit)
    ebit = to_float(statement.operating_income)
    ni = to_float(statement.net_income)
    eps_val = to_float(statement.eps)
    equity = to_float(statement.shareholder_equity)
    total_debt = to_float(statement.total_debt)
    curr_assets = to_float(statement.total_current_assets)
    curr_liab = to_float(statement.total_current_liabilities)
    bvps = to_float(statement.book_value_per_share)
    ocf = to_float(statement.operating_cash_flow)
    fcf = to_float(statement.free_cash_flow)

    # Margins
    gross_margin = None
    if rev is not None and rev > 0 and gp is not None:
        gross_margin = round((gp / rev) * 100.0, 2)

    op_margin = None
    if rev is not None and rev > 0 and ebit is not None:
        op_margin = round((ebit / rev) * 100.0, 2)

    net_margin = None
    if rev is not None and rev > 0 and ni is not None:
        net_margin = round((ni / rev) * 100.0, 2)

    # ROE (Return on Equity): Net Income / Shareholder Equity
    roe = None
    if equity is not None and equity > 0 and ni is not None:
        roe = round((ni / equity) * 100.0, 2)

    # Debt-to-Equity
    de = None
    if equity is not None and equity > 0 and total_debt is not None:
        de = round(total_debt / equity, 2)

    # Current Ratio
    cr = None
    if curr_liab is not None and curr_liab > 0 and curr_assets is not None:
        cr = round(curr_assets / curr_liab, 2)

    # Valuation Ratios (P/E and P/B)
    pe = None
    pb = None
    if latest_price is not None and latest_price > 0:
        if eps_val is not None and eps_val > 0:
            pe = round(latest_price / eps_val, 2)
        if bvps is not None and bvps > 0:
            pb = round(latest_price / bvps, 2)
        elif equity is not None and equity > 0 and statement.diluted_shares is not None:
            shares = to_float(statement.diluted_shares)
            if shares and shares > 0:
                derived_bvps = equity / shares
                if derived_bvps > 0:
                    pb = round(latest_price / derived_bvps, 2)

    return FundamentalRatios(
        period_type=statement.period_type,
        fiscal_year=statement.fiscal_year,
        fiscal_quarter=statement.fiscal_quarter,
        period_end_date=str(statement.period_end_date),
        currency=statement.currency,
        is_synthetic=statement.is_synthetic,
        price=round(latest_price, 2) if latest_price is not None else None,
        pe_ratio=pe,
        pb_ratio=pb,
        gross_margin_pct=gross_margin,
        operating_margin_pct=op_margin,
        net_margin_pct=net_margin,
        roe_pct=roe,
        debt_to_equity=de,
        current_ratio=cr,
        revenue=round(rev, 2) if rev is not None else None,
        net_income=round(ni, 2) if ni is not None else None,
        operating_income=round(ebit, 2) if ebit is not None else None,
        eps=round(eps_val, 2) if eps_val is not None else None,
        total_assets=round(to_float(statement.total_assets), 2) if statement.total_assets is not None else None,
        total_debt=round(total_debt, 2) if total_debt is not None else None,
        shareholder_equity=round(equity, 2) if equity is not None else None,
        operating_cash_flow=round(ocf, 2) if ocf is not None else None,
        free_cash_flow=round(fcf, 2) if fcf is not None else None,
    )
