import csv
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import io
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session

from app.core.logging import logger
from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.instrument import Instrument
from app.models.price_history import PriceHistory
from app.providers.demo import DemoMarketDataProvider
from app.schemas.market_data import PriceBar


def get_or_create_data_source(
    db: Session,
    provider_name: str,
    dataset: str,
    terms_url: Optional[str] = None,
) -> DataSource:
    """Finds or creates a DataSource reference."""
    source = (
        db.query(DataSource)
        .filter(DataSource.provider_name == provider_name, DataSource.dataset == dataset)
        .first()
    )
    if not source:
        source = DataSource(
            provider_name=provider_name,
            dataset=dataset,
            terms_url=terms_url,
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    return source


def upsert_price_bar(
    db: Session,
    instrument_id: uuid.UUID,
    bar: PriceBar,
    provider_id: Optional[uuid.UUID] = None,
) -> PriceHistory:
    """
    Idempotently upserts a single daily price record.
    Prevents duplicates by updating existing row if (instrument_id, trade_date, provider_id) matches.
    """
    existing = (
        db.query(PriceHistory)
        .filter(
            PriceHistory.instrument_id == instrument_id,
            PriceHistory.trade_date == bar.trade_date,
            PriceHistory.provider_id == provider_id,
        )
        .first()
    )

    if existing:
        existing.open = bar.open
        existing.high = bar.high
        existing.low = bar.low
        existing.close = bar.close
        existing.adjusted_close = bar.adjusted_close
        existing.volume = bar.volume
        existing.currency = bar.currency
        existing.is_demo = bar.is_demo
        existing.retrieved_at = datetime.now(timezone.utc)
        return existing

    record = PriceHistory(
        instrument_id=instrument_id,
        provider_id=provider_id,
        trade_date=bar.trade_date,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        adjusted_close=bar.adjusted_close,
        volume=bar.volume,
        currency=bar.currency,
        is_demo=bar.is_demo,
    )
    db.add(record)
    return record


class CsvMarketDataIngestionService:
    """Validates and imports market price data from CSV content."""

    @staticmethod
    def parse_and_validate_csv(csv_content: str) -> Tuple[List[PriceBar], List[str]]:
        """
        Parses CSV string, validates each row against financial domain rules,
        and returns (valid_bars, error_messages).
        """
        valid_bars: List[PriceBar] = []
        errors: List[str] = []

        if "\x00" in csv_content:
            return [], ["Binary or corrupted CSV content detected. Only valid UTF-8 text files are permitted."]

        reader = csv.DictReader(io.StringIO(csv_content))
        if not reader.fieldnames:
            return [], ["CSV file is empty or missing headers"]

        # Standardize header names
        normalized_fieldnames = {f.strip().lower(): f for f in reader.fieldnames}
        date_key = normalized_fieldnames.get("date") or normalized_fieldnames.get("trade_date")
        close_key = normalized_fieldnames.get("close")

        if not date_key or not close_key:
            return [], ["CSV must contain at least 'trade_date' (or 'date') and 'close' columns"]

        open_key = normalized_fieldnames.get("open")
        high_key = normalized_fieldnames.get("high")
        low_key = normalized_fieldnames.get("low")
        adj_close_key = normalized_fieldnames.get("adjusted_close") or normalized_fieldnames.get("adj_close")
        volume_key = normalized_fieldnames.get("volume")
        currency_key = normalized_fieldnames.get("currency")

        for row_idx, row in enumerate(reader, start=2):
            raw_date = row.get(date_key, "").strip()
            raw_close = row.get(close_key, "").strip()

            if not raw_date or not raw_close:
                errors.append(f"Row {row_idx}: Missing required date or close price")
                continue

            try:
                parsed_date = date.fromisoformat(raw_date)
            except ValueError:
                errors.append(f"Row {row_idx}: Invalid date format '{raw_date}' (expected YYYY-MM-DD)")
                continue

            try:
                d_close = Decimal(raw_close)
                if d_close <= 0:
                    errors.append(f"Row {row_idx}: Close price must be positive")
                    continue
            except (InvalidOperation, ValueError):
                errors.append(f"Row {row_idx}: Invalid numeric close price '{raw_close}'")
                continue

            d_open: Optional[Decimal] = None
            if open_key and row.get(open_key, "").strip():
                try:
                    d_open = Decimal(row[open_key].strip())
                    if d_open <= 0:
                        errors.append(f"Row {row_idx}: Open price must be positive")
                        continue
                except (InvalidOperation, ValueError):
                    errors.append(f"Row {row_idx}: Invalid numeric open price '{row[open_key]}'")
                    continue

            d_high: Optional[Decimal] = None
            if high_key and row.get(high_key, "").strip():
                try:
                    d_high = Decimal(row[high_key].strip())
                    if d_high <= 0:
                        errors.append(f"Row {row_idx}: High price must be positive")
                        continue
                except (InvalidOperation, ValueError):
                    errors.append(f"Row {row_idx}: Invalid numeric high price '{row[high_key]}'")
                    continue

            d_low: Optional[Decimal] = None
            if low_key and row.get(low_key, "").strip():
                try:
                    d_low = Decimal(row[low_key].strip())
                    if d_low <= 0:
                        errors.append(f"Row {row_idx}: Low price must be positive")
                        continue
                except (InvalidOperation, ValueError):
                    errors.append(f"Row {row_idx}: Invalid numeric low price '{row[low_key]}'")
                    continue

            d_adj_close: Optional[Decimal] = None
            if adj_close_key and row.get(adj_close_key, "").strip():
                try:
                    d_adj_close = Decimal(row[adj_close_key].strip())
                except (InvalidOperation, ValueError):
                    errors.append(f"Row {row_idx}: Invalid numeric adjusted_close '{row[adj_close_key]}'")
                    continue

            volume: Optional[int] = None
            if volume_key and row.get(volume_key, "").strip():
                try:
                    volume = int(float(row[volume_key].strip()))
                    if volume < 0:
                        errors.append(f"Row {row_idx}: Volume cannot be negative")
                        continue
                except ValueError:
                    errors.append(f"Row {row_idx}: Invalid volume '{row[volume_key]}'")
                    continue

            currency = row.get(currency_key, "INR").strip() if currency_key else "INR"

            # Validate high >= low, high >= open, high >= close, etc.
            try:
                bar = PriceBar(
                    trade_date=parsed_date,
                    open=d_open,
                    high=d_high,
                    low=d_low,
                    close=d_close,
                    adjusted_close=d_adj_close or d_close,
                    volume=volume,
                    currency=currency,
                    is_demo=False,
                )
                valid_bars.append(bar)
            except ValueError as val_err:
                errors.append(f"Row {row_idx}: {val_err}")

        return valid_bars, errors

    @classmethod
    def ingest_csv(
        cls,
        db: Session,
        instrument_id: uuid.UUID,
        csv_content: str,
        provider_name: str = "csv_upload",
        dataset: str = "daily_prices",
    ) -> IngestionRun:
        """
        Executes ingestion run from CSV content, saving valid rows idempotently
        and logging results into IngestionRun.
        """
        run = IngestionRun(
            provider_name=provider_name,
            dataset=dataset,
            status="running",
            rows_processed=0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        valid_bars, errors = cls.parse_and_validate_csv(csv_content)
        data_source = get_or_create_data_source(db, provider_name, dataset)

        count = 0
        try:
            for bar in valid_bars:
                upsert_price_bar(db, instrument_id=instrument_id, bar=bar, provider_id=data_source.id)
                count += 1
            db.commit()

            run.rows_processed = count
            run.completed_at = datetime.now(timezone.utc)
            if errors and count > 0:
                run.status = "partial"
                run.error_message = "; ".join(errors[:10])
            elif errors and count == 0:
                run.status = "failed"
                run.error_message = "; ".join(errors[:10])
            else:
                run.status = "success"

        except Exception as exc:
            db.rollback()
            run.status = "failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(timezone.utc)
            logger.error(f"Ingestion run failed: {exc}", exc_info=True)

        db.commit()
        db.refresh(run)
        return run


def seed_demo_market_data(db: Session) -> Tuple[int, int]:
    """
    Seeds deterministic synthetic demo data for Indian equities if not present.
    Returns (instruments_count, prices_count).
    """
    provider = DemoMarketDataProvider()
    source = get_or_create_data_source(
        db,
        provider_name=provider.provider_name,
        dataset=provider.dataset,
        terms_url=provider.terms_url,
    )

    instruments_created = 0
    prices_created = 0

    run = IngestionRun(
        provider_name=provider.provider_name,
        dataset=provider.dataset,
        status="running",
        rows_processed=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()

    try:
        instruments_data = provider.fetch_instruments()
        for inst_data in instruments_data:
            existing_inst = (
                db.query(Instrument)
                .filter(Instrument.exchange == inst_data.exchange, Instrument.symbol == inst_data.symbol)
                .first()
            )
            if not existing_inst:
                inst = Instrument(
                    exchange=inst_data.exchange,
                    symbol=inst_data.symbol,
                    isin=inst_data.isin,
                    company_name=inst_data.company_name,
                    instrument_type=inst_data.instrument_type,
                    sector=inst_data.sector,
                    industry=inst_data.industry,
                    currency=inst_data.currency,
                    is_active=inst_data.is_active,
                    is_demo=inst_data.is_demo,
                )
                db.add(inst)
                db.commit()
                db.refresh(inst)
                existing_inst = inst
                instruments_created += 1

            # Fetch and upsert price bars
            prices = provider.fetch_daily_prices(inst_data.symbol)
            for bar in prices:
                upsert_price_bar(
                    db,
                    instrument_id=existing_inst.id,
                    bar=bar,
                    provider_id=source.id,
                )
                prices_created += 1

        db.commit()
        run.status = "success"
        run.rows_processed = prices_created
        run.completed_at = datetime.now(timezone.utc)
    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.error_message = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        logger.error(f"Seed demo data failed: {exc}", exc_info=True)

    db.commit()
    return instruments_created, prices_created
