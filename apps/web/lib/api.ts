export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface UserPreferences {
  theme: string;
  avatar_preset: string;
  color_mode: string;
  reduced_motion: boolean;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  demo_mode: boolean;
  database: string;
  version: string;
}

export interface PriceBar {
  trade_date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  adjusted_close: number | null;
  volume: number | null;
  currency: string;
  is_demo: boolean;
}

export interface Instrument {
  id: string;
  exchange: string;
  symbol: string;
  isin: string | null;
  company_name: string;
  instrument_type: string;
  sector: string | null;
  industry: string | null;
  currency: string;
  is_active: boolean;
  is_demo: boolean;
  created_at: string;
}

export interface InstrumentDetail extends Instrument {
  latest_price: PriceBar | null;
  data_source: string | null;
  as_of: string | null;
}

export interface PaginatedInstruments {
  items: Instrument[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface IndicatorPoint {
  trade_date: string;
  close: number;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  ema_12: number | null;
  ema_26: number | null;
  rsi_14: number | null;
  macd_line: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
  bb_bandwidth: number | null;
  bb_percent_b: number | null;
}

export interface TechnicalSummary {
  trend: string;
  trend_description: string;
  rsi_state: string;
  rsi_value: number | null;
  macd_state: string;
  macd_histogram: number | null;
  bb_state: string;
  golden_cross: boolean | null;
}

export interface TechnicalAnalysisResponse {
  instrument_id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  count: number;
  summary: TechnicalSummary;
  points: IndicatorPoint[];
}

export interface FinancialStatement {
  id: string;
  period_type: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  period_start_date: string | null;
  period_end_date: string;
  filing_date: string | null;
  currency: string;
  is_synthetic: boolean;
  revenue: number | null;
  cost_of_goods_sold: number | null;
  gross_profit: number | null;
  operating_expenses: number | null;
  operating_income: number | null;
  interest_expense: number | null;
  tax_expense: number | null;
  net_income: number | null;
  eps: number | null;
  diluted_shares: number | null;
  cash_and_equivalents: number | null;
  total_current_assets: number | null;
  total_non_current_assets: number | null;
  total_assets: number | null;
  total_current_liabilities: number | null;
  total_long_term_debt: number | null;
  total_debt: number | null;
  total_liabilities: number | null;
  shareholder_equity: number | null;
  book_value_per_share: number | null;
  operating_cash_flow: number | null;
  capital_expenditures: number | null;
  free_cash_flow: number | null;
  investing_cash_flow: number | null;
  financing_cash_flow: number | null;
  net_change_in_cash: number | null;
}

export interface FundamentalRatios {
  period_type: string;
  fiscal_year: number;
  fiscal_quarter: number | null;
  period_end_date: string;
  currency: string;
  is_synthetic: boolean;
  price: number | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  gross_margin_pct: number | null;
  operating_margin_pct: number | null;
  net_margin_pct: number | null;
  roe_pct: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  revenue: number | null;
  net_income: number | null;
  operating_income: number | null;
  eps: number | null;
  total_assets: number | null;
  total_debt: number | null;
  shareholder_equity: number | null;
  operating_cash_flow: number | null;
  free_cash_flow: number | null;
}

export interface CompanyFundamentalsResponse {
  instrument_id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  currency: string;
  is_synthetic: boolean;
  disclaimer: string;
  statements: FinancialStatement[];
  latest_ratios: FundamentalRatios | null;
}

export interface InstrumentComparisonMetrics {
  instrument_id: string;
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string | null;
  currency: string;
  latest_price: number | null;
  period_return_pct: number | null;
  annualized_volatility_pct: number | null;
  max_drawdown_pct: number | null;
  sma_20: number | null;
  sma_50: number | null;
  sma_200: number | null;
  rsi_14: number | null;
  macd_signal_state: string;
  ma_cross_state: string | null;
  pe_ratio: number | null;
  pb_ratio: number | null;
  roe_pct: number | null;
  net_margin_pct: number | null;
  operating_margin_pct: number | null;
  debt_to_equity: number | null;
  current_ratio: number | null;
  has_fundamentals: boolean;
}

export interface NormalizedChartPoint {
  trade_date: string;
  prices: Record<string, number | null>;
}

export interface EquityComparisonResponse {
  period: string;
  start_date: string | null;
  end_date: string | null;
  instruments: InstrumentComparisonMetrics[];
  normalized_chart: NormalizedChartPoint[];
  is_demo: boolean;
  disclaimer: string;
}

export interface PriceHistoryResponse {
  instrument_id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  currency: string;
  is_demo: boolean;
  data_source: string | null;
  count: number;
  start_date: string | null;
  end_date: string | null;
  prices: PriceBar[];
}

export interface Portfolio {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  base_currency: string;
  created_at: string;
  updated_at: string;
}

export interface PortfolioTransaction {
  id: string;
  portfolio_id: string;
  instrument_id: string | null;
  instrument_symbol: string | null;
  instrument_name: string | null;
  transaction_type: string;
  trade_date: string;
  trade_timestamp: string;
  quantity: number;
  price_per_unit: number;
  fees: number;
  cash_amount: number;
  notes: string | null;
  idempotency_key: string | null;
  created_at: string;
}

export interface PortfolioHolding {
  instrument_id: string;
  symbol: string;
  exchange: string;
  company_name: string;
  sector: string;
  quantity: number;
  average_buy_price: number;
  current_price: number | null;
  cost_basis: number;
  market_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  realized_pnl: number;
  allocation_percent: number;
  price_date: string | null;
  is_stale: boolean;
  is_demo: boolean;
}

export interface AssetAllocation {
  name: string;
  symbol: string | null;
  value: number;
  percentage: number;
  type?: string;
}

export interface SectorAllocation {
  sector: string;
  value: number;
  percentage: number;
}

export interface PortfolioValuation {
  portfolio_id: string;
  portfolio_name: string;
  base_currency: string;
  as_of_date: string;
  total_value: number;
  cash_balance: number;
  holdings_market_value: number;
  cost_basis: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  realized_pnl: number;
  total_pnl: number;
  holdings: PortfolioHolding[];
  asset_allocations: AssetAllocation[];
  sector_allocations: SectorAllocation[];
}

export interface PortfolioPerformance {
  twr_percent: number | null;
  xirr_percent: number | null;
  annualized_volatility_percent: number | null;
  sharpe_ratio: number | null;
  max_drawdown_percent: number;
  risk_free_rate_percent: number;
  timeline_days: number;
}

export interface EquityPoint {
  date: string;
  total_value: number;
  cash: number;
  holdings_value: number;
  net_external_flow: number;
}

export interface ApiError {
  detail: string;
}

export interface MutualFund {
  id: string;
  scheme_code: string;
  isin: string | null;
  scheme_name: string;
  amc_name: string;
  category: string;
  subcategory: string;
  plan_type: string;
  option_type: string;
  benchmark_name: string | null;
  expense_ratio: number | null;
  aum_crores: number | null;
  fund_manager: string | null;
  crisil_rating: number | null;
  is_active: boolean;
  is_demo: boolean;
  created_at: string;
  updated_at: string;
}

export interface FundNAVPoint {
  nav_date: string;
  nav: number;
  repurchase_price: number | null;
  sale_price: number | null;
  is_demo: boolean;
}

export interface MutualFundDetail extends MutualFund {
  latest_nav: FundNAVPoint | null;
  trailing_returns: Record<string, number | null> | null;
}

export interface PaginatedMutualFunds {
  items: MutualFund[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface FundNAVHistoryResponse {
  fund_id: string;
  scheme_code: string;
  scheme_name: string;
  amc_name: string;
  category: string;
  subcategory: string;
  is_demo: boolean;
  count: number;
  start_date: string | null;
  end_date: string | null;
  navs: FundNAVPoint[];
}

export interface RollingReturnsSummary {
  mean_pct: number | null;
  median_pct: number | null;
  min_pct: number | null;
  max_pct: number | null;
  positive_periods_pct: number | null;
  samples: number;
}

export interface FundAnalyticsResponse {
  fund_id: string;
  scheme_code: string;
  scheme_name: string;
  amc_name: string;
  category: string;
  subcategory: string;
  trailing_returns: Record<string, number | null>;
  rolling_returns_1y: RollingReturnsSummary;
  rolling_returns_3y: RollingReturnsSummary;
  volatility_pct: number | null;
  max_drawdown_pct: number;
  is_demo: boolean;
  disclaimer: string;
}

export interface SIPInstallmentPoint {
  installment_number: number;
  scheduled_date: string;
  executed_date: string;
  nav: number;
  amount: number;
  units: number;
  total_units: number;
  cumulative_invested: number;
}

export interface SIPCalculatorResponse {
  fund_id: string;
  scheme_name: string;
  monthly_amount: number;
  start_date: string;
  end_date: string;
  installments_count: number;
  total_invested: number;
  final_value: number;
  total_profit: number;
  absolute_return_pct: number;
  xirr_pct: number | null;
  units_accumulated: number;
  latest_nav: number;
  installments: SIPInstallmentPoint[];
  timeline: Array<{
    date: string;
    invested: number;
    value: number;
    units: number;
    nav: number;
  }>;
  is_demo: boolean;
  disclaimer: string;
}

export interface LumpSumCalculatorResponse {
  fund_id: string;
  scheme_name: string;
  initial_investment: number;
  start_date: string;
  end_date: string;
  start_nav: number;
  end_nav: number;
  units_accumulated: number;
  final_value: number;
  total_profit: number;
  absolute_return_pct: number;
  cagr_pct: number | null;
  duration_days: number;
  timeline: Array<{
    date: string;
    invested: number;
    value: number;
    nav: number;
  }>;
  is_demo: boolean;
  disclaimer: string;
}

export interface FundComparisonItem {
  fund_id: string;
  scheme_code: string;
  scheme_name: string;
  amc_name: string;
  category: string;
  subcategory: string;
  plan_type: string;
  option_type: string;
  crisil_rating: number | null;
  expense_ratio: number | null;
  aum_crores: number | null;
  latest_nav: number | null;
  period_return_pct: number | null;
  cagr_pct: number | null;
  annualized_volatility_pct: number | null;
  max_drawdown_pct: number;
  observation_count: number;
}

export interface FundComparisonResponse {
  period: string;
  start_date: string | null;
  end_date: string | null;
  funds: FundComparisonItem[];
  normalized_chart: Array<{
    date: string;
    navs: Record<string, number | null>;
  }>;
  is_demo: boolean;
  disclaimer: string;
}

export interface FundCategoriesResponse {
  categories: string[];
  subcategories: string[];
  amcs: string[];
}

export interface NewsSentiment {
  id: string;
  model_name: string;
  positive_score: number;
  negative_score: number;
  neutral_score: number;
  sentiment_label: string;
  confidence: number;
  analyzed_at: string;
}

export interface LinkedInstrumentSummary {
  id: string;
  symbol: string;
  company_name: string;
  match_method: string;
  match_confidence: number;
}

export interface NewsArticle {
  id: string;
  source_id: string;
  source_name: string | null;
  title: string;
  short_description: string | null;
  canonical_url: string;
  published_at: string;
  ingested_at: string;
  category: string;
  language: string;
  is_demo: boolean;
  sentiment: NewsSentiment | null;
  linked_instruments: LinkedInstrumentSummary[];
}

export interface PaginatedNewsArticles {
  items: NewsArticle[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface SentimentTrendSummary {
  total_articles: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
  positive_pct: number;
  negative_pct: number;
  neutral_pct: number;
  net_sentiment_score: number;
  overall_classification: string;
  average_confidence: number;
  time_window_days: number;
  is_demo: boolean;
  disclaimer: string;
}

export interface MacroObservationPoint {
  id: string;
  observation_date: string;
  value: number;
  release_timestamp: string | null;
  is_demo: boolean;
}

export interface MacroSeries {
  series_id: string;
  name: string;
  unit: string;
  source: string;
  description: string | null;
  frequency: string;
  is_demo: boolean;
  latest_observation: MacroObservationPoint | null;
  observations: MacroObservationPoint[];
}

export interface WatchlistItem {
  id: string;
  instrument_id: string;
  symbol: string;
  company_name: string;
  exchange: string;
  sector: string | null;
  added_at: string;
  notes: string | null;
}

export interface Watchlist {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  items: WatchlistItem[];
  latest_news: NewsArticle[];
}

export interface UserAlert {
  id: string;
  user_id: string;
  instrument_id: string | null;
  alert_type: string;
  keyword: string | null;
  target_sentiment: string | null;
  is_active: boolean;
  created_at: string;
}

export interface AlertNotification {
  id: string;
  user_id: string;
  alert_id: string | null;
  article_id: string | null;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface ResearchStrategy {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  strategy_type: string;
  version: number;
  parameters: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface BacktestMetrics {
  starting_capital: number;
  ending_equity: number;
  net_profit: number;
  total_return_pct: number;
  cagr_pct: number | null;
  annualized_volatility_pct: number;
  sharpe_ratio: number | null;
  sortino_ratio: number | null;
  max_drawdown_pct: number;
  calmar_ratio: number | null;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate_pct: number;
  profit_factor: number | null;
  avg_trade_pnl: number;
  avg_winning_trade: number;
  avg_losing_trade: number;
  total_fees_paid: number;
  total_slippage_paid: number;
  exposure_pct: number;
  benchmark_return_pct: number;
  duration_days: number;
}

export interface BacktestTrade {
  id: string;
  run_id: string;
  side: string;
  signal_date: string;
  execution_date: string;
  quantity: number;
  execution_price: number;
  fees: number;
  slippage_cost: number;
  cash_after: number;
  position_after: number;
  realized_pnl: number | null;
  pnl_pct: number | null;
}

export interface BacktestEquityPoint {
  point_date: string;
  equity: number;
  cash: number;
  position_value: number;
  drawdown_pct: number;
  benchmark_equity: number | null;
}

export interface BacktestRun {
  id: string;
  strategy_id: string | null;
  user_id: string;
  instrument_id: string;
  instrument_ticker?: string | null;
  instrument_name?: string | null;
  strategy_name?: string | null;
  strategy_type?: string | null;
  starting_capital: number;
  start_date: string;
  end_date: string;
  fee_rate: number;
  slippage_bps: number;
  status: string;
  metrics?: BacktestMetrics | null;
  dataset_fingerprint?: string | null;
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface GridSearchResultItem {
  params: Record<string, any>;
  in_sample_return_pct: number;
  in_sample_sharpe: number | null;
  in_sample_max_dd_pct: number;
  out_of_sample_return_pct: number;
  out_of_sample_sharpe: number | null;
  out_of_sample_max_dd_pct: number;
  overfitting_warning: boolean;
  status: string;
  error_message?: string | null;
}

export interface GridSearchResponse {
  strategy_type: string;
  instrument_id: string;
  combinations_tested: number;
  results: GridSearchResultItem[];
  best_params: Record<string, any> | null;
  summary: string;
}

export interface BacktestComparisonItem {
  run_id: string;
  strategy_name?: string | null;
  strategy_type?: string | null;
  instrument_ticker?: string | null;
  start_date: string;
  end_date: string;
  starting_capital: number;
  fee_rate: number;
  slippage_bps: number;
  metrics?: BacktestMetrics | null;
}

export interface BacktestComparisonResponse {
  runs: BacktestComparisonItem[];
}

// ==========================================
// AI Copilot Interfaces (Milestone 8)
// ==========================================

export interface AIToolExecution {
  tool_name: string;
  status: string;
  result: Record<string, any>;
  execution_time_ms?: number;
}

export interface AIRetrievalSource {
  citation_key: string;
  source_title: string;
  source_url?: string | null;
  snippet: string;
  relevance_score: number;
}

export interface AIMessage {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  provider?: string;
  model_name?: string;
  tokens_used?: number;
  latency_ms?: number;
  created_at: string;
  tool_executions: AIToolExecution[];
  retrieval_sources: AIRetrievalSource[];
}

export interface AIConversation {
  id: string;
  user_id: string;
  title: string;
  context_module?: string | null;
  context_entity_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetailResponse extends AIConversation {
  messages: AIMessage[];
}

export interface ChatTurnResponse {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  content: string;
  role: string;
  provider: string;
  model_name: string;
  tokens_used: number;
  latency_ms: number;
  tool_executions: AIToolExecution[];
  retrieval_sources: AIRetrievalSource[];
  created_at: string;
}

export interface ToolCatalogItem {
  name: string;
  description: string;
  parameters: Record<string, any>;
}

export interface EvaluationResponse {
  evaluation_id: string;
  total_cases: number;
  passed_cases: number;
  accuracy_pct: number;
  results: Record<string, any>[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(message: string, status: number, detail?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail || message;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  headers.set("Accept", "application/json");
  headers.set("X-Requested-With", "XMLHttpRequest");

  const config: RequestInit = {
    ...options,
    headers,
    credentials: "include",
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorDetail = `Request failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (typeof errorJson.detail === "string") {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.detail)) {
          errorDetail = errorJson.detail
            .map((err: { msg?: string; loc?: string[] }) => err.msg || "Invalid input")
            .join(", ");
        }
      } catch {
        // Response was not JSON
      }
      throw new ApiError(errorDetail, response.status, errorDetail);
    }

    const text = await response.text();
    return text ? (JSON.parse(text) as T) : ({} as T);
  } catch (err: unknown) {
    if (err instanceof ApiError) {
      throw err;
    }
    if (err instanceof Error) {
      throw new ApiError(err.message, 0);
    }
    throw new ApiError("An unexpected network error occurred", 0);
  }
}

export const api = {
  getHealth: () => request<HealthResponse>("/health"),

  register: (name: string, email: string, password: string) =>
    request<TokenResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    request<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    }),

  getMe: () => request<User>("/api/v1/users/me"),

  updateProfile: (data: { name: string }) =>
    request<User>("/api/v1/users/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  changePassword: (data: { current_password: string; new_password: string }) =>
    request<{ message: string }>("/api/v1/users/change-password", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Market Data APIs
  listInstruments: (params: {
    page?: number;
    size?: number;
    exchange?: string;
    sector?: string;
    instrument_type?: string;
    is_active?: boolean;
  } = {}) => {
    const query = new URLSearchParams();
    if (params.page) query.set("page", params.page.toString());
    if (params.size) query.set("size", params.size.toString());
    if (params.exchange) query.set("exchange", params.exchange);
    if (params.sector) query.set("sector", params.sector);
    if (params.instrument_type) query.set("instrument_type", params.instrument_type);
    if (params.is_active !== undefined) query.set("is_active", params.is_active.toString());
    const qs = query.toString();
    return request<PaginatedInstruments>(`/api/v1/instruments${qs ? `?${qs}` : ""}`);
  },

  searchInstruments: (q: string, limit: number = 10) =>
    request<Instrument[]>(`/api/v1/instruments/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  getInstrument: (id: string) =>
    request<InstrumentDetail>(`/api/v1/instruments/${id}`),

  getInstrumentPrices: (
    id: string,
    params: { start_date?: string; end_date?: string; limit?: number } = {}
  ) => {
    const query = new URLSearchParams();
    if (params.start_date) query.set("start_date", params.start_date);
    if (params.end_date) query.set("end_date", params.end_date);
    if (params.limit) query.set("limit", params.limit.toString());
    const qs = query.toString();
    return request<PriceHistoryResponse>(`/api/v1/instruments/${id}/prices${qs ? `?${qs}` : ""}`);
  },

  getInstrumentTechnicals: (id: string) =>
    request<TechnicalAnalysisResponse>(`/api/v1/instruments/${id}/technicals`),

  getInstrumentFundamentals: (id: string) =>
    request<CompanyFundamentalsResponse>(`/api/v1/instruments/${id}/fundamentals`),

  compareInstruments: (ids: string[], period: string = "1Y") =>
    request<EquityComparisonResponse>(
      `/api/v1/instruments/compare?ids=${ids.join(",")}&period=${encodeURIComponent(period)}`
    ),

  seedMarketData: () =>
    request<{ status: string; message: string; instruments_created: number; prices_created: number }>(
      "/api/v1/instruments/seed",
      { method: "POST" }
    ),

  // Portfolio Intelligence MVP APIs
  listPortfolios: () =>
    request<Portfolio[]>("/api/v1/portfolios"),

  createPortfolio: (data: { name: string; description?: string; base_currency?: string }) =>
    request<Portfolio>("/api/v1/portfolios", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getPortfolio: (id: string) =>
    request<Portfolio>(`/api/v1/portfolios/${id}`),

  recordPortfolioTransaction: (
    portfolioId: string,
    data: {
      transaction_type: string;
      trade_date: string;
      quantity?: number;
      price_per_unit?: number;
      fees?: number;
      instrument_id?: string;
      notes?: string;
      idempotency_key?: string;
    }
  ) =>
    request<PortfolioTransaction>(`/api/v1/portfolios/${portfolioId}/transactions`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listPortfolioTransactions: (portfolioId: string, limit: number = 100, offset: number = 0) =>
    request<PortfolioTransaction[]>(
      `/api/v1/portfolios/${portfolioId}/transactions?limit=${limit}&offset=${offset}`
    ),

  getPortfolioValuation: (portfolioId: string, asOfDate?: string) =>
    request<PortfolioValuation>(
      `/api/v1/portfolios/${portfolioId}/valuation${asOfDate ? `?as_of_date=${asOfDate}` : ""}`
    ),

  getPortfolioPerformance: (portfolioId: string, asOfDate?: string, riskFreeRate?: number) => {
    const query = new URLSearchParams();
    if (asOfDate) query.set("as_of_date", asOfDate);
    if (riskFreeRate !== undefined) query.set("risk_free_rate", riskFreeRate.toString());
    const qs = query.toString();
    return request<PortfolioPerformance>(
      `/api/v1/portfolios/${portfolioId}/performance${qs ? `?${qs}` : ""}`
    );
  },

  getPortfolioHistory: (portfolioId: string, asOfDate?: string) =>
    request<EquityPoint[]>(
      `/api/v1/portfolios/${portfolioId}/history${asOfDate ? `?as_of_date=${asOfDate}` : ""}`
    ),

  // Mutual Fund Intelligence (FundScope) APIs
  listFunds: (params?: {
    page?: number;
    size?: number;
    category?: string;
    subcategory?: string;
    amc?: string;
    plan_type?: string;
    q?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.category && params.category !== "All") query.set("category", params.category);
    if (params?.subcategory && params.subcategory !== "All") query.set("subcategory", params.subcategory);
    if (params?.amc && params.amc !== "All") query.set("amc", params.amc);
    if (params?.plan_type && params.plan_type !== "All") query.set("plan_type", params.plan_type);
    if (params?.q) query.set("q", params.q);
    const qs = query.toString();
    return request<PaginatedMutualFunds>(`/api/v1/funds${qs ? `?${qs}` : ""}`);
  },

  searchFunds: (q: string, limit: number = 10) =>
    request<MutualFund[]>(`/api/v1/funds/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  getFundCategories: () =>
    request<FundCategoriesResponse>("/api/v1/funds/categories"),

  getFund: (id: string) =>
    request<MutualFundDetail>(`/api/v1/funds/${id}`),

  getFundNAVHistory: (id: string, params?: { start_date?: string; end_date?: string; limit?: number }) => {
    const query = new URLSearchParams();
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    if (params?.limit) query.set("limit", params.limit.toString());
    const qs = query.toString();
    return request<FundNAVHistoryResponse>(`/api/v1/funds/${id}/nav${qs ? `?${qs}` : ""}`);
  },

  getFundAnalytics: (id: string) =>
    request<FundAnalyticsResponse>(`/api/v1/funds/${id}/analytics`),

  calculateSIP: (
    fundId: string,
    data: {
      monthly_amount: number;
      start_date: string;
      end_date?: string;
      sip_day?: number;
    }
  ) =>
    request<SIPCalculatorResponse>(`/api/v1/funds/${fundId}/sip-calculator`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  calculateLumpSum: (
    fundId: string,
    data: {
      amount: number;
      start_date: string;
      end_date?: string;
    }
  ) =>
    request<LumpSumCalculatorResponse>(`/api/v1/funds/${fundId}/lump-sum-calculator`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  compareFunds: (ids: string[], period: string = "1Y") =>
    request<FundComparisonResponse>(
      `/api/v1/funds/compare?ids=${ids.join(",")}&period=${encodeURIComponent(period)}`
    ),

  seedFunds: () =>
    request<{ status: string; message: string; funds_created: number; nav_rows_created: number }>(
      "/api/v1/funds/seed",
      { method: "POST" }
    ),

  // MarketPulse APIs
  listNews: (params?: {
    page?: number;
    size?: number;
    category?: string;
    sentiment?: string;
    instrument_id?: string;
    q?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const query = new URLSearchParams();
    if (params?.page) query.set("page", params.page.toString());
    if (params?.size) query.set("size", params.size.toString());
    if (params?.category && params.category !== "All") query.set("category", params.category);
    if (params?.sentiment && params.sentiment !== "All") query.set("sentiment", params.sentiment);
    if (params?.instrument_id) query.set("instrument_id", params.instrument_id);
    if (params?.q) query.set("q", params.q);
    if (params?.start_date) query.set("start_date", params.start_date);
    if (params?.end_date) query.set("end_date", params.end_date);
    const qs = query.toString();
    return request<PaginatedNewsArticles>(`/api/v1/market/news${qs ? `?${qs}` : ""}`);
  },

  searchNews: (q: string, limit: number = 10) =>
    request<NewsArticle[]>(`/api/v1/market/news/search?q=${encodeURIComponent(q)}&limit=${limit}`),

  getNewsCategories: () =>
    request<{ categories: string[] }>("/api/v1/market/news/categories"),

  getNewsArticle: (id: string) =>
    request<NewsArticle>(`/api/v1/market/news/${id}`),

  getCompanyNews: (instrumentId: string, limit: number = 20) =>
    request<NewsArticle[]>(`/api/v1/market/instruments/${instrumentId}/news?limit=${limit}`),

  getSectorNews: (sector: string, limit: number = 20) =>
    request<NewsArticle[]>(`/api/v1/market/sectors/${encodeURIComponent(sector)}/news?limit=${limit}`),

  getSentimentSummary: (params?: { days?: number; instrument_id?: string; sector?: string }) => {
    const query = new URLSearchParams();
    if (params?.days) query.set("days", params.days.toString());
    if (params?.instrument_id) query.set("instrument_id", params.instrument_id);
    if (params?.sector) query.set("sector", params.sector);
    const qs = query.toString();
    return request<SentimentTrendSummary>(`/api/v1/market/sentiment/summary${qs ? `?${qs}` : ""}`);
  },

  listMacroSeries: () =>
    request<MacroSeries[]>("/api/v1/market/macro/series"),

  getMacroSeriesHistory: (seriesId: string) =>
    request<MacroSeries>(`/api/v1/market/macro/series/${seriesId}`),

  seedMarketPulse: () =>
    request<{ status: string; message: string; articles_ingested: number; series_created: number }>(
      "/api/v1/market/seed",
      { method: "POST" }
    ),

  listWatchlists: () =>
    request<Watchlist[]>("/api/v1/market/watchlists"),

  createWatchlist: (data: { name: string; description?: string }) =>
    request<Watchlist>("/api/v1/market/watchlists", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getWatchlist: (id: string) =>
    request<Watchlist>(`/api/v1/market/watchlists/${id}`),

  updateWatchlist: (id: string, data: { name?: string; description?: string }) =>
    request<Watchlist>(`/api/v1/market/watchlists/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteWatchlist: (id: string) =>
    request<void>(`/api/v1/market/watchlists/${id}`, {
      method: "DELETE",
    }),

  addWatchlistItem: (watchlistId: string, data: { instrument_id: string; notes?: string }) =>
    request<WatchlistItem>(`/api/v1/market/watchlists/${watchlistId}/items`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  removeWatchlistItem: (watchlistId: string, instrumentId: string) =>
    request<void>(`/api/v1/market/watchlists/${watchlistId}/items/${instrumentId}`, {
      method: "DELETE",
    }),

  listAlerts: () =>
    request<UserAlert[]>("/api/v1/market/alerts"),

  createAlert: (data: { instrument_id?: string; alert_type?: string; keyword?: string; target_sentiment?: string }) =>
    request<UserAlert>("/api/v1/market/alerts", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteAlert: (id: string) =>
    request<void>(`/api/v1/market/alerts/${id}`, {
      method: "DELETE",
    }),

  listNotifications: (limit: number = 20) =>
    request<AlertNotification[]>(`/api/v1/market/notifications?limit=${limit}`),

  markNotificationRead: (id: string) =>
    request<AlertNotification>(`/api/v1/market/notifications/${id}/read`, {
      method: "PUT",
    }),

  // QuantLab Strategy & Backtesting APIs
  listStrategies: () =>
    request<ResearchStrategy[]>("/api/v1/quantlab/strategies"),

  createStrategy: (data: {
    name: string;
    description?: string;
    strategy_type: string;
    parameters: Record<string, any>;
  }) =>
    request<ResearchStrategy>("/api/v1/quantlab/strategies", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getStrategy: (id: string) =>
    request<ResearchStrategy>(`/api/v1/quantlab/strategies/${id}`),

  updateStrategy: (
    id: string,
    data: { name?: string; description?: string; parameters?: Record<string, any> }
  ) =>
    request<ResearchStrategy>(`/api/v1/quantlab/strategies/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteStrategy: (id: string) =>
    request<void>(`/api/v1/quantlab/strategies/${id}`, {
      method: "DELETE",
    }),

  runStrategyBacktest: (
    strategyId: string,
    data: {
      instrument_id: string;
      start_date: string;
      end_date: string;
      starting_capital?: number;
      fee_rate?: number;
      slippage_bps?: number;
    }
  ) =>
    request<BacktestRun>(`/api/v1/quantlab/strategies/${strategyId}/backtest`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  runInstantBacktest: (data: {
    strategy_type: string;
    parameters: Record<string, any>;
    instrument_id: string;
    start_date: string;
    end_date: string;
    starting_capital?: number;
    fee_rate?: number;
    slippage_bps?: number;
  }) =>
    request<BacktestRun>("/api/v1/quantlab/backtest/instant", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listBacktestRuns: (limit: number = 20, offset: number = 0) =>
    request<BacktestRun[]>(`/api/v1/quantlab/runs?limit=${limit}&offset=${offset}`),

  getBacktestRun: (id: string) =>
    request<BacktestRun>(`/api/v1/quantlab/runs/${id}`),

  getBacktestTrades: (id: string) =>
    request<BacktestTrade[]>(`/api/v1/quantlab/runs/${id}/trades`),

  getBacktestEquity: (id: string) =>
    request<BacktestEquityPoint[]>(`/api/v1/quantlab/runs/${id}/equity`),

  deleteBacktestRun: (id: string) =>
    request<void>(`/api/v1/quantlab/runs/${id}`, {
      method: "DELETE",
    }),

  compareBacktestRuns: (runIds: string[]) =>
    request<BacktestComparisonResponse>("/api/v1/quantlab/runs/compare", {
      method: "POST",
      body: JSON.stringify({ run_ids: runIds }),
    }),

  runGridSearch: (data: {
    strategy_type: string;
    param_grid: Record<string, any[]>;
    instrument_id: string;
    start_date: string;
    end_date: string;
    starting_capital?: number;
    fee_rate?: number;
    slippage_bps?: number;
    train_ratio?: number;
  }) =>
    request<GridSearchResponse>("/api/v1/quantlab/experiments/grid-search", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // AI Copilot Endpoints (Milestone 8)
  listConversations: () =>
    request<AIConversation[]>("/api/v1/ai/conversations"),

  createConversation: (data: {
    title?: string;
    context_module?: string;
    context_entity_id?: string;
  }) =>
    request<AIConversation>("/api/v1/ai/conversations", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getConversation: (id: string) =>
    request<ConversationDetailResponse>(`/api/v1/ai/conversations/${id}`),

  deleteConversation: (id: string) =>
    request<void>(`/api/v1/ai/conversations/${id}`, {
      method: "DELETE",
    }),

  sendMessage: (
    conversationId: string,
    data: {
      content: string;
      context_module?: string;
      context_entity_id?: string;
    }
  ) =>
    request<ChatTurnResponse>(`/api/v1/ai/conversations/${conversationId}/messages`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listAiTools: () =>
    request<ToolCatalogItem[]>("/api/v1/ai/tools"),

  runAiEvaluation: () =>
    request<EvaluationResponse>("/api/v1/ai/evaluate", {
      method: "POST",
    }),

  // User Preferences & Themes
  getUserPreferences: () =>
    request<UserPreferences>("/api/v1/users/me/preferences"),

  updateUserPreferences: (data: Partial<UserPreferences>) =>
    request<UserPreferences>("/api/v1/users/me/preferences", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
};
