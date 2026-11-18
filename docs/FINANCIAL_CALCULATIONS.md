# Financial Calculations and Methodology

Every metric must have a documented formula, input frequency, annualisation rule, missing-data policy and tests.

## Return calculations
Simple period return:
`(ending_value - beginning_value - external_cash_flows_adjusted) / beginning_value`
For portfolios with external deposits/withdrawals, do not use this naive formula as a general performance measure. Implement and label:
- Time-weighted return (TWR): neutralises external cash-flow timing by linking sub-period returns.
- Money-weighted return (MWR/XIRR): solves for the discount rate that makes dated cash flows' net present value zero.

## CAGR
`(ending_value / beginning_value) ** (1 / years) - 1`
Only use when beginning/ending values and duration are valid and no confusing external cash flows are present.

## Volatility
Standard deviation of periodic returns multiplied by square root of periods per year. State whether daily, weekly or monthly returns are used and the annualisation factor.

## Beta
Covariance(asset returns, benchmark returns) / variance(benchmark returns), using aligned observations and a stated lookback period.

## Sharpe ratio
Mean periodic excess return / standard deviation of periodic returns, annualised consistently. State the risk-free-rate assumption and frequency.

## Maximum drawdown
For a wealth index, calculate the largest percentage decline from a previous running peak to a subsequent trough.

## Technical indicators
- SMA(n): rolling arithmetic mean of n closes.
- EMA(n): exponentially weighted mean with documented smoothing convention.
- RSI(n): use a documented Wilder or alternative smoothing convention; do not mix conventions.
- MACD: document fast EMA, slow EMA and signal EMA periods.

## Fund SIP
Create dated cash flows for contributions and terminal redemption value. Calculate XIRR using actual dates. Clearly state NAV date conventions and any assumed execution day.

## Portfolio optimisation
Use return and covariance estimates from a documented lookback period. Explain sensitivity to estimates and constraints. Never present optimiser output as a guaranteed best portfolio.

## Backtesting
- Signal generated using data available at signal time.
- Execution no earlier than the next bar unless an explicitly justified execution model is used.
- Include transaction costs and slippage.
- Apply corporate-action policy consistently.
- Avoid survivorship bias where historical universe data is unavailable.
- Store exact parameters, dates, data version and assumptions for reproducibility.
- Distinguish gross and net returns.
