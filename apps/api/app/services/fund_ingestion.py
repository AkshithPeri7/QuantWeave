"""
Mutual Fund NAV Data Ingestion Service for QuantWeave.

Supports CSV ingestion with:
- Strict numerical validation (NAV > 0)
- Date formatting checks
- Duplicate prevention via upsert
- Audit reporting
"""

import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import io
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.models.mutual_fund import MutualFund, FundNAVHistory


class FundCSVIngestionService:
    """Parses, validates, and upserts mutual fund NAV history from CSV files."""

    @staticmethod
    def parse_and_validate_csv(
        db: Session,
        csv_content: str,
        default_fund_id: Optional[uuid.UUID] = None,
    ) -> Tuple[List[dict], List[str]]:
        """
        Parses CSV string, validates columns and numbers.
        Returns (valid_rows, error_messages).
        
        Expected headers:
        - date / nav_date (YYYY-MM-DD)
        - nav (positive decimal)
        - scheme_code (optional if default_fund_id provided)
        - repurchase_price (optional)
        - sale_price (optional)
        """
        errors: List[str] = []
        valid_rows: List[dict] = []

        reader = csv.DictReader(io.StringIO(csv_content))
        if not reader.fieldnames:
            return [], ["CSV file is empty or missing header row."]

        # Normalize header keys
        headers = {col.lower().strip(): col for col in reader.fieldnames}

        date_col = next((headers[k] for k in ["nav_date", "date", "trade_date"] if k in headers), None)
        nav_col = next((headers[k] for k in ["nav", "net_asset_value", "close"] if k in headers), None)
        code_col = next((headers[k] for k in ["scheme_code", "code"] if k in headers), None)
        repurchase_col = next((headers[k] for k in ["repurchase_price", "repurchase"] if k in headers), None)
        sale_col = next((headers[k] for k in ["sale_price", "sale"] if k in headers), None)

        if not date_col or not nav_col:
            return [], [f"Missing required CSV columns: 'date' and 'nav' are mandatory. Found: {list(headers.keys())}"]

        # Cache fund lookup by code
        code_to_fund: dict = {}

        for line_num, row in enumerate(reader, start=2):
            raw_date = row.get(date_col, "").strip()
            raw_nav = row.get(nav_col, "").strip()

            if not raw_date or not raw_nav:
                errors.append(f"Row {line_num}: Empty date or NAV.")
                continue

            # Parse date
            try:
                parsed_date = date.fromisoformat(raw_date)
            except ValueError:
                errors.append(f"Row {line_num}: Invalid date '{raw_date}'. Expected format: YYYY-MM-DD.")
                continue

            # Parse NAV
            try:
                nav_val = Decimal(raw_nav)
                if nav_val <= 0:
                    errors.append(f"Row {line_num}: NAV must be strictly positive (> 0), got '{raw_nav}'.")
                    continue
            except (InvalidOperation, ValueError):
                errors.append(f"Row {line_num}: Invalid numeric NAV '{raw_nav}'.")
                continue

            # Resolve fund_id
            fund_id = default_fund_id
            if code_col and row.get(code_col, "").strip():
                code = row[code_col].strip()
                if code not in code_to_fund:
                    f = db.query(MutualFund).filter(MutualFund.scheme_code == code).first()
                    code_to_fund[code] = f.id if f else None
                fund_id = code_to_fund[code]
                if not fund_id:
                    errors.append(f"Row {line_num}: Mutual fund scheme code '{code}' not found.")
                    continue

            if not fund_id:
                errors.append(f"Row {line_num}: No mutual fund identified (specify scheme_code or fund_id).")
                continue

            # Repurchase and sale prices
            repurchase_val: Optional[Decimal] = None
            if repurchase_col and row.get(repurchase_col, "").strip():
                try:
                    repurchase_val = Decimal(row[repurchase_col].strip())
                except (InvalidOperation, ValueError):
                    pass

            sale_val: Optional[Decimal] = None
            if sale_col and row.get(sale_col, "").strip():
                try:
                    sale_val = Decimal(row[sale_col].strip())
                except (InvalidOperation, ValueError):
                    pass

            valid_rows.append({
                "fund_id": fund_id,
                "nav_date": parsed_date,
                "nav": nav_val,
                "repurchase_price": repurchase_val,
                "sale_price": sale_val,
            })

        return valid_rows, errors

    @classmethod
    def ingest_nav_records(cls, db: Session, records: List[dict], is_demo: bool = True) -> int:
        """
        Idempotently inserts or updates NAV records to prevent duplicate dates per fund.
        """
        inserted_or_updated = 0
        for rec in records:
            existing = (
                db.query(FundNAVHistory)
                .filter(
                    FundNAVHistory.fund_id == rec["fund_id"],
                    FundNAVHistory.nav_date == rec["nav_date"],
                )
                .first()
            )
            if existing:
                existing.nav = rec["nav"]
                existing.repurchase_price = rec.get("repurchase_price")
                existing.sale_price = rec.get("sale_price")
                existing.is_demo = is_demo
            else:
                new_nav = FundNAVHistory(
                    fund_id=rec["fund_id"],
                    nav_date=rec["nav_date"],
                    nav=rec["nav"],
                    repurchase_price=rec.get("repurchase_price"),
                    sale_price=rec.get("sale_price"),
                    is_demo=is_demo,
                )
                db.add(new_nav)
            inserted_or_updated += 1

        db.commit()
        return inserted_or_updated
