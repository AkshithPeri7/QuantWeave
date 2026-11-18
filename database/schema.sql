-- QuantWeave initial PostgreSQL logical schema.
-- Use Alembic migrations for application deployments.
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS data_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(120) NOT NULL,
    dataset VARCHAR(80) NOT NULL,
    terms_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(provider_name, dataset)
);

CREATE TABLE IF NOT EXISTS instruments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(80) NOT NULL,
    isin VARCHAR(20),
    company_name VARCHAR(255) NOT NULL,
    instrument_type VARCHAR(30) NOT NULL DEFAULT 'equity',
    sector VARCHAR(120),
    industry VARCHAR(120),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_demo BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(exchange, symbol)
);

CREATE TABLE IF NOT EXISTS price_history (
    id BIGSERIAL PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES data_sources(id),
    trade_date DATE NOT NULL,
    open NUMERIC(20,6),
    high NUMERIC(20,6),
    low NUMERIC(20,6),
    close NUMERIC(20,6) NOT NULL,
    adjusted_close NUMERIC(20,6),
    volume BIGINT,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    is_demo BOOLEAN NOT NULL DEFAULT false,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (high IS NULL OR low IS NULL OR high >= low),
    CHECK (volume IS NULL OR volume >= 0),
    UNIQUE(instrument_id, trade_date, provider_id)
);
CREATE INDEX IF NOT EXISTS ix_price_history_instrument_date
    ON price_history(instrument_id, trade_date DESC);

CREATE TABLE IF NOT EXISTS financial_statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES data_sources(id),
    statement_type VARCHAR(30) NOT NULL,
    period_start DATE,
    period_end DATE NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    revenue NUMERIC(24,4),
    ebit NUMERIC(24,4),
    net_income NUMERIC(24,4),
    total_assets NUMERIC(24,4),
    total_debt NUMERIC(24,4),
    shareholder_equity NUMERIC(24,4),
    eps NUMERIC(20,6),
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(instrument_id, statement_type, period_end, provider_id)
);

CREATE TABLE IF NOT EXISTS portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    benchmark_symbol VARCHAR(80),
    base_currency CHAR(3) NOT NULL DEFAULT 'INR',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_portfolios_user ON portfolios(user_id);

CREATE TABLE IF NOT EXISTS portfolio_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    instrument_id UUID REFERENCES instruments(id),
    transaction_type VARCHAR(30) NOT NULL,
    quantity NUMERIC(24,8) NOT NULL DEFAULT 0,
    unit_price NUMERIC(20,6) NOT NULL DEFAULT 0,
    fees NUMERIC(20,6) NOT NULL DEFAULT 0,
    cash_amount NUMERIC(20,6),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    trade_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (quantity >= 0),
    CHECK (unit_price >= 0),
    CHECK (fees >= 0)
);
CREATE INDEX IF NOT EXISTS ix_portfolio_tx_portfolio_date
    ON portfolio_transactions(portfolio_id, trade_at);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    invested_value NUMERIC(24,6),
    market_value NUMERIC(24,6),
    total_pnl NUMERIC(24,6),
    currency CHAR(3) NOT NULL DEFAULT 'INR',
    methodology_version VARCHAR(40) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(portfolio_id, snapshot_date, methodology_version)
);

CREATE TABLE IF NOT EXISTS mutual_funds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scheme_code VARCHAR(40) NOT NULL UNIQUE,
    isin VARCHAR(20),
    scheme_name VARCHAR(255) NOT NULL,
    fund_house VARCHAR(180),
    category VARCHAR(120),
    plan_type VARCHAR(40),
    option_type VARCHAR(40),
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS fund_nav_history (
    id BIGSERIAL PRIMARY KEY,
    fund_id UUID NOT NULL REFERENCES mutual_funds(id) ON DELETE CASCADE,
    provider_id UUID REFERENCES data_sources(id),
    nav_date DATE NOT NULL,
    nav NUMERIC(20,8) NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(fund_id, nav_date, provider_id)
);
CREATE INDEX IF NOT EXISTS ix_fund_nav_date ON fund_nav_history(fund_id, nav_date DESC);

CREATE TABLE IF NOT EXISTS fund_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id UUID NOT NULL REFERENCES mutual_funds(id) ON DELETE CASCADE,
    instrument_id UUID REFERENCES instruments(id),
    holding_date DATE NOT NULL,
    weight NUMERIC(12,8),
    quantity NUMERIC(24,8),
    source_url TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (weight IS NULL OR (weight >= 0 AND weight <= 1))
);
CREATE INDEX IF NOT EXISTS ix_fund_holdings_fund_date ON fund_holdings(fund_id, holding_date);

CREATE TABLE IF NOT EXISTS news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(120) NOT NULL,
    external_id VARCHAR(255),
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ,
    content_hash VARCHAR(128),
    summary TEXT,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(provider_name, external_id)
);

CREATE TABLE IF NOT EXISTS news_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES news_articles(id) ON DELETE CASCADE,
    event_type VARCHAR(80),
    sentiment_label VARCHAR(30),
    sentiment_score NUMERIC(8,6),
    confidence NUMERIC(8,6),
    model_version VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS news_instruments (
    news_event_id UUID NOT NULL REFERENCES news_events(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id) ON DELETE CASCADE,
    relevance_score NUMERIC(8,6),
    PRIMARY KEY(news_event_id, instrument_id)
);

CREATE TABLE IF NOT EXISTS strategies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    strategy_json JSONB NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS backtests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES strategies(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital NUMERIC(24,6) NOT NULL,
    assumptions_json JSONB NOT NULL,
    data_version VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CHECK (end_date >= start_date),
    CHECK (initial_capital > 0)
);

CREATE TABLE IF NOT EXISTS backtest_metrics (
    backtest_id UUID PRIMARY KEY REFERENCES backtests(id) ON DELETE CASCADE,
    total_return NUMERIC(16,8),
    cagr NUMERIC(16,8),
    sharpe NUMERIC(16,8),
    sortino NUMERIC(16,8),
    max_drawdown NUMERIC(16,8),
    win_rate NUMERIC(16,8),
    profit_factor NUMERIC(16,8)
);

CREATE TABLE IF NOT EXISTS backtest_trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backtest_id UUID NOT NULL REFERENCES backtests(id) ON DELETE CASCADE,
    instrument_id UUID NOT NULL REFERENCES instruments(id),
    side VARCHAR(10) NOT NULL,
    quantity NUMERIC(24,8) NOT NULL,
    entry_at TIMESTAMPTZ NOT NULL,
    entry_price NUMERIC(20,6) NOT NULL,
    exit_at TIMESTAMPTZ,
    exit_price NUMERIC(20,6),
    fees NUMERIC(20,6) NOT NULL DEFAULT 0,
    pnl NUMERIC(24,6)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(180),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    module VARCHAR(40) NOT NULL,
    insight_type VARCHAR(80) NOT NULL,
    input_reference JSONB,
    output_json JSONB NOT NULL,
    model_name VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ai_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    insight_id UUID NOT NULL REFERENCES ai_insights(id) ON DELETE CASCADE,
    source_type VARCHAR(60) NOT NULL,
    source_id VARCHAR(255),
    source_url TEXT,
    excerpt TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_name VARCHAR(120) NOT NULL,
    dataset VARCHAR(80) NOT NULL,
    status VARCHAR(30) NOT NULL,
    rows_processed INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(80),
    resource_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
