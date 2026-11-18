from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.ingestion_run import IngestionRun
from app.models.instrument import Instrument
from app.models.price_history import PriceHistory
from app.providers.demo import DemoMarketDataProvider
from app.schemas.market_data import PriceBar
from app.services.ingestion import (
    CsvMarketDataIngestionService,
    seed_demo_market_data,
    upsert_price_bar,
)


def test_demo_provider_deterministic():
    provider = DemoMarketDataProvider()
    instruments = provider.fetch_instruments()
    assert len(instruments) == 10
    assert any(i.symbol == "RELIANCE" for i in instruments)
    assert any(i.symbol == "TCS" for i in instruments)

    prices1 = provider.fetch_daily_prices("RELIANCE")
    prices2 = provider.fetch_daily_prices("RELIANCE")
    assert len(prices1) == 250
    # Deterministic output check:
    assert prices1[0].close == prices2[0].close
    assert prices1[-1].close == prices2[-1].close


def test_invalid_ohlc_validation():
    # Test high < low
    with pytest.raises(ValueError, match="High price .* cannot be less than low price"):
        PriceBar(
            trade_date=date(2026, 1, 15),
            open=Decimal("100.00"),
            high=Decimal("90.00"),  # high < low
            low=Decimal("95.00"),
            close=Decimal("92.00"),
        )

    # Test high < open
    with pytest.raises(ValueError, match="High price .* cannot be less than open price"):
        PriceBar(
            trade_date=date(2026, 1, 15),
            open=Decimal("110.00"),
            high=Decimal("105.00"),  # high < open
            low=Decimal("95.00"),
            close=Decimal("100.00"),
        )

    # Test low > close
    with pytest.raises(ValueError, match="Low price .* cannot be greater than close price"):
        PriceBar(
            trade_date=date(2026, 1, 15),
            open=Decimal("100.00"),
            high=Decimal("105.00"),
            low=Decimal("98.00"),
            close=Decimal("95.00"),  # close < low
        )

    # Test non-positive close
    with pytest.raises(ValueError):
        PriceBar(
            trade_date=date(2026, 1, 15),
            close=Decimal("0.00"),
        )

    # Test negative volume
    with pytest.raises(ValueError):
        PriceBar(
            trade_date=date(2026, 1, 15),
            close=Decimal("100.00"),
            volume=-50,
        )


def test_seed_demo_market_data(db_session: Session):
    inst_count, prices_count = seed_demo_market_data(db_session)
    assert inst_count == 10
    assert prices_count == 10 * 250

    # Verify instruments and price records in database
    instruments = db_session.query(Instrument).all()
    assert len(instruments) == 10
    for inst in instruments:
        assert inst.is_demo is True
        assert inst.exchange == "NSE"

    reliance = db_session.query(Instrument).filter(Instrument.symbol == "RELIANCE").first()
    assert reliance is not None
    prices = (
        db_session.query(PriceHistory)
        .filter(PriceHistory.instrument_id == reliance.id)
        .all()
    )
    assert len(prices) == 250


def test_duplicate_price_ingestion_idempotent(db_session: Session):
    # Create an instrument
    inst = Instrument(
        exchange="NSE",
        symbol="TESTCO",
        company_name="Test Company Ltd",
        currency="INR",
        is_demo=True,
    )
    db_session.add(inst)
    db_session.commit()
    db_session.refresh(inst)

    source = DataSource(provider_name="test_provider", dataset="test_daily")
    db_session.add(source)
    db_session.commit()

    bar1 = PriceBar(
        trade_date=date(2026, 6, 1),
        open=Decimal("100.00"),
        high=Decimal("105.00"),
        low=Decimal("98.00"),
        close=Decimal("102.50"),
        volume=10000,
    )
    upsert_price_bar(db_session, inst.id, bar1, source.id)
    db_session.commit()

    count_after_first = (
        db_session.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .count()
    )
    assert count_after_first == 1

    # Ingest updated price for the exact same date
    bar1_updated = PriceBar(
        trade_date=date(2026, 6, 1),
        open=Decimal("100.00"),
        high=Decimal("106.00"),  # updated
        low=Decimal("98.00"),
        close=Decimal("104.00"),  # updated
        volume=12000,
    )
    upsert_price_bar(db_session, inst.id, bar1_updated, source.id)
    db_session.commit()

    # Must still be exactly 1 record, with updated values
    count_after_second = (
        db_session.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id)
        .count()
    )
    assert count_after_second == 1

    record = (
        db_session.query(PriceHistory)
        .filter(PriceHistory.instrument_id == inst.id, PriceHistory.trade_date == date(2026, 6, 1))
        .first()
    )
    assert record.close == Decimal("104.00")
    assert record.high == Decimal("106.00")
    assert record.volume == 12000


def test_csv_ingestion_service(db_session: Session):
    inst = Instrument(
        exchange="NSE",
        symbol="CSVCO",
        company_name="CSV Company Ltd",
        currency="INR",
        is_demo=False,
    )
    db_session.add(inst)
    db_session.commit()

    valid_csv = """trade_date,open,high,low,close,volume
2026-05-01,50.00,52.50,49.50,51.20,150000
2026-05-02,51.20,53.00,50.80,52.40,165000
2026-05-03,52.40,54.00,52.00,53.80,180000
"""
    run = CsvMarketDataIngestionService.ingest_csv(
        db=db_session,
        instrument_id=inst.id,
        csv_content=valid_csv,
    )
    assert run.status == "success"
    assert run.rows_processed == 3

    prices = db_session.query(PriceHistory).filter(PriceHistory.instrument_id == inst.id).all()
    assert len(prices) == 3


def test_csv_ingestion_with_invalid_rows(db_session: Session):
    inst = Instrument(
        exchange="NSE",
        symbol="MIXCO",
        company_name="Mixed Valid/Invalid Ltd",
        currency="INR",
    )
    db_session.add(inst)
    db_session.commit()

    mixed_csv = """date,open,high,low,close,volume
2026-05-01,100,105,95,102,1000
invalid-date,100,105,95,102,1000
2026-05-03,100,90,95,92,1000
"""
    run = CsvMarketDataIngestionService.ingest_csv(
        db=db_session,
        instrument_id=inst.id,
        csv_content=mixed_csv,
    )
    assert run.status == "partial"
    assert run.rows_processed == 1  # only first row valid
    assert "Invalid date format" in run.error_message
    assert "High price" in run.error_message


def test_api_list_instruments_pagination_and_filtering(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)

    # Test pagination
    res = client.get("/api/v1/instruments?page=1&size=4")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 10
    assert len(data["items"]) == 4
    assert data["page"] == 1
    assert data["size"] == 4
    assert data["pages"] == 3

    # Test filtering by sector
    res_tech = client.get("/api/v1/instruments?sector=Information Technology")
    assert res_tech.status_code == 200
    tech_data = res_tech.json()
    assert tech_data["total"] == 2  # TCS, INFY
    symbols = [item["symbol"] for item in tech_data["items"]]
    assert "TCS" in symbols
    assert "INFY" in symbols

    # Test filtering by exchange
    res_nse = client.get("/api/v1/instruments?exchange=NSE")
    assert res_nse.status_code == 200
    assert res_nse.json()["total"] == 10


def test_api_search_instruments(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)

    # Search ticker
    res = client.get("/api/v1/instruments/search?q=rel")
    assert res.status_code == 200
    matches = res.json()
    assert len(matches) >= 1
    assert matches[0]["symbol"] == "RELIANCE"

    # Search company name
    res_name = client.get("/api/v1/instruments/search?q=consultancy")
    assert res_name.status_code == 200
    matches_name = res_name.json()
    assert len(matches_name) >= 1
    assert matches_name[0]["symbol"] == "TCS"

    # Non-existent query
    res_empty = client.get("/api/v1/instruments/search?q=nonexistentticker123")
    assert res_empty.status_code == 200
    assert len(res_empty.json()) == 0


def test_api_get_instrument_by_id(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    res = client.get(f"/api/v1/instruments/{tcs.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["symbol"] == "TCS"
    assert data["company_name"] == "Tata Consultancy Services Limited"
    assert data["latest_price"] is not None
    assert "close" in data["latest_price"]
    assert data["is_demo"] is True


def test_api_get_instrument_not_found(client: TestClient):
    random_id = uuid.uuid4()
    res = client.get(f"/api/v1/instruments/{random_id}")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_api_get_instrument_prices_filtering(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)
    infy = db_session.query(Instrument).filter(Instrument.symbol == "INFY").first()

    # Get all prices
    res_all = client.get(f"/api/v1/instruments/{infy.id}/prices")
    assert res_all.status_code == 200
    all_data = res_all.json()
    assert all_data["count"] == 250
    assert len(all_data["prices"]) == 250
    # Prices must be sorted ascending by date
    dates = [p["trade_date"] for p in all_data["prices"]]
    assert dates == sorted(dates)

    # Date range filtering
    start = dates[100]
    end = dates[150]
    res_range = client.get(f"/api/v1/instruments/{infy.id}/prices?start_date={start}&end_date={end}")
    assert res_range.status_code == 200
    range_data = res_range.json()
    assert range_data["count"] == 51
    assert range_data["start_date"] == start
    assert range_data["end_date"] == end


def test_api_get_instrument_prices_invalid_range(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)
    infy = db_session.query(Instrument).filter(Instrument.symbol == "INFY").first()

    res = client.get(
        f"/api/v1/instruments/{infy.id}/prices?start_date=2026-11-01&end_date=2026-01-01"
    )
    assert res.status_code == 400
    assert "start_date cannot be after end_date" in res.json()["detail"]


def test_api_get_prices_empty_instrument(client: TestClient, db_session: Session):
    empty_inst = Instrument(
        exchange="NSE",
        symbol="EMPTYCO",
        company_name="Empty Instrument Ltd",
        currency="INR",
    )
    db_session.add(empty_inst)
    db_session.commit()

    res = client.get(f"/api/v1/instruments/{empty_inst.id}/prices")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 0
    assert data["prices"] == []
    assert data["start_date"] is None
    assert data["end_date"] is None
