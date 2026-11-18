"""
Integration tests for Milestone 3 Equity Intelligence API routes:
- GET /api/v1/instruments/{id}/technicals
- GET /api/v1/instruments/{id}/fundamentals
- GET /api/v1/instruments/compare
- Security auditing on CSV upload size & validation
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.instrument import Instrument
from app.providers.financial_fixtures import seed_demo_financial_statements
from app.services.ingestion import seed_demo_market_data


def test_api_instrument_technicals(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)
    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    assert tcs is not None

    res = client.get(f"/api/v1/instruments/{tcs.id}/technicals")
    assert res.status_code == 200
    data = res.json()

    assert data["symbol"] == "TCS"
    assert data["count"] == 250
    assert "summary" in data
    assert data["summary"]["trend"] in ["Bullish", "Bearish", "Neutral"]
    assert data["summary"]["rsi_state"] in ["Overbought", "Oversold", "Neutral"]
    assert "points" in data
    assert len(data["points"]) == 250

    # Verify latest point has non-null technical values
    last_pt = data["points"][-1]
    assert last_pt["close"] > 0
    assert last_pt["sma_20"] is not None
    assert last_pt["sma_50"] is not None
    assert last_pt["sma_200"] is not None
    assert last_pt["rsi_14"] is not None
    assert last_pt["bb_upper"] is not None
    assert last_pt["bb_lower"] is not None


def test_api_instrument_fundamentals(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)
    seed_demo_financial_statements(db_session)

    infy = db_session.query(Instrument).filter(Instrument.symbol == "INFY").first()
    assert infy is not None

    res = client.get(f"/api/v1/instruments/{infy.id}/fundamentals")
    assert res.status_code == 200
    data = res.json()

    assert data["symbol"] == "INFY"
    assert data["is_synthetic"] is True
    assert "DEMO SYNTHETIC FINANCIALS" in data["disclaimer"]
    assert len(data["statements"]) >= 3

    # Check calculated ratios
    assert data["latest_ratios"] is not None
    ratios = data["latest_ratios"]
    assert ratios["gross_margin_pct"] is not None
    assert ratios["operating_margin_pct"] is not None
    assert ratios["roe_pct"] is not None
    assert ratios["pe_ratio"] is not None
    assert ratios["pb_ratio"] is not None


def test_api_compare_equities_success(client: TestClient, db_session: Session):
    seed_demo_market_data(db_session)
    seed_demo_financial_statements(db_session)

    tcs = db_session.query(Instrument).filter(Instrument.symbol == "TCS").first()
    infy = db_session.query(Instrument).filter(Instrument.symbol == "INFY").first()
    reliance = db_session.query(Instrument).filter(Instrument.symbol == "RELIANCE").first()

    ids_query = f"{tcs.id},{infy.id},{reliance.id}"
    res = client.get(f"/api/v1/instruments/compare?ids={ids_query}&period=6M")
    assert res.status_code == 200
    data = res.json()

    assert data["period"] == "6M"
    assert len(data["instruments"]) == 3
    symbols = [m["symbol"] for m in data["instruments"]]
    assert "TCS" in symbols
    assert "INFY" in symbols
    assert "RELIANCE" in symbols

    # Check performance and risk metrics
    for inst_m in data["instruments"]:
        assert inst_m["latest_price"] is not None
        assert inst_m["period_return_pct"] is not None
        assert inst_m["annualized_volatility_pct"] is not None
        assert inst_m["max_drawdown_pct"] is not None
        assert inst_m["rsi_14"] is not None

    # Check normalized chart
    assert len(data["normalized_chart"]) > 0
    # First day normalized values should be 100.0
    first_pt = data["normalized_chart"][0]
    assert first_pt["prices"]["TCS"] == 100.0
    assert first_pt["prices"]["INFY"] == 100.0


def test_api_compare_equities_validation(client: TestClient):
    # Test more than 4 instruments
    u1, u2, u3, u4, u5 = [str(uuid.uuid4()) for _ in range(5)]
    res_too_many = client.get(f"/api/v1/instruments/compare?ids={u1},{u2},{u3},{u4},{u5}")
    assert res_too_many.status_code == 400
    assert "maximum of 4 instruments" in res_too_many.json()["detail"]

    # Test invalid UUID format
    res_bad_uuid = client.get("/api/v1/instruments/compare?ids=invalid-uuid-123")
    assert res_bad_uuid.status_code == 400
    assert "Invalid UUID format" in res_bad_uuid.json()["detail"]


def test_csv_upload_size_limit_and_binary_check(
    client: TestClient, db_session: Session, test_user_token: str
):
    inst = Instrument(
        exchange="NSE",
        symbol="TESTCO",
        company_name="Test Co Ltd",
        currency="INR",
    )
    db_session.add(inst)
    db_session.commit()

    # 1. Test unauthenticated request is blocked (Phase E Security)
    res_unauth = client.post(
        f"/api/v1/instruments/{inst.id}/ingest/csv",
        content="trade_date,close\n2026-01-01,100\n",
        headers={"Content-Type": "text/plain"},
    )
    assert res_unauth.status_code == 401

    auth_headers = {
        "Authorization": f"Bearer {test_user_token}",
        "Content-Type": "text/plain",
    }

    # 2. Test null byte rejection when authenticated
    bad_csv = "trade_date,close\n2026-01-01,100\x00\n"
    res_binary = client.post(
        f"/api/v1/instruments/{inst.id}/ingest/csv",
        content=bad_csv,
        headers=auth_headers,
    )
    assert res_binary.status_code == 400
    assert "prohibited binary null characters" in res_binary.json()["detail"]

    # 3. Test empty payload rejection
    res_empty = client.post(
        f"/api/v1/instruments/{inst.id}/ingest/csv",
        content="   ",
        headers=auth_headers,
    )
    assert res_empty.status_code == 400
    assert "cannot be empty" in res_empty.json()["detail"]
