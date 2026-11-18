# QuantLab — Quantitative Backtesting & Strategy Engine Methodology

QuantLab is the algorithmic backtesting and strategy evaluation engine in QuantWeave. It is engineered to simulate realistic market conditions, enforce strict temporal execution boundaries, and eliminate the pitfalls common to academic or hobbyist backtesters.

---

## 1. Elimination of Look-Ahead Bias

### The Problem
Look-ahead bias occurs when a backtesting algorithm utilizes information at time $t$ that was not known or accessible when trading decisions were made.
- **Example of Flawed Engine**: Indicator evaluates on Day $t$ Close, and the engine executes the Buy order at Day $t$ Open (impossible time travel) or Day $t$ Close (unrealistic without market-on-close auction guarantees).

### The QuantLab Execution Model: Next-Bar Open
QuantLab strictly enforces **Next-Bar Open Execution**:
1. At the end of trading day $t$, all historical price data up to bar $t$ Close is available.
2. Technical indicators (SMA, EMA, RSI, MACD) are evaluated against bar $t$ Close.
3. If a signal condition triggers (e.g., Fast SMA crosses above Slow SMA), an order is staged for **Day $t+1$**.
4. The order is executed at the **Open price of Day $t+1$**.
5. No prices or volumes from day $t+1$ or later are accessible to the indicator calculations.

```
Bar t-1 [Open - High - Low - Close]  --> History
Bar t   [Open - High - Low - Close]  --> SIGNAL GENERATED AT CLOSE
Bar t+1 [OPEN]                       --> ORDER EXECUTED HERE
```

---

## 2. Friction & Real-World Execution Modeling

A frictionless backtest drastically overestimates returns, especially for strategies with higher turnover. QuantLab incorporates realistic market frictions:

### 1. Brokerage & Exchange Fees
- Configured in basis points (bps) or fixed percentage (e.g., 10 bps / 0.10%).
- Deducted directly from cash upon execution:
  $$\text{Fee} = \text{Order Value} \times \frac{\text{Commission Bps}}{10,000}$$

### 2. Execution Slippage
- Simulates market impact and bid-ask spread crossing:
  - **BUY Order**:
    $$\text{Executed Price} = \text{Open}_{t+1} \times \left(1 + \frac{\text{Slippage Bps}}{10,000}\right)$$
  - **SELL Order**:
    $$\text{Executed Price} = \text{Open}_{t+1} \times \left(1 - \frac{\text{Slippage Bps}}{10,000}\right)$$

### 3. Long-Only Cash Protection Guard
- Short selling and negative cash borrowing are disallowed in base simulation modes.
- Before placing a BUY order, the engine checks available cash:
  $$\text{Max Shares} = \left\lfloor \frac{\text{Available Cash}}{\text{Executed Price} \times (1 + \text{Fee Rate})} \right\rfloor$$
- If cash is insufficient to buy at least 1 whole share, the order is safely rejected.

---

## 3. Parameter Grid Search & Overfitting Prevention

### The Dangers of Data Snooping
Testing hundreds of combinations (e.g. SMA windows 5 through 50) on a single historical dataset almost always produces high Sharpe ratios that collapse in live trading due to curve-fitting historical noise.

### In-Sample (Train) vs. Out-of-Sample (Test) Partitioning
QuantLab implements automated chronological partitioning:
1. **In-Sample Period (First 70% of Chronological Bars)**:
   - Evaluates the strategy across the parameter grid.
   - Ranks parameter sets by Sharpe Ratio, Total Return, or Win Rate.
2. **Out-of-Sample Period (Remaining 30% of Chronological Bars)**:
   - Tests top candidate parameter sets on unseen data.
   - Computes the **Performance Degradation Ratio**:
     $$\text{Degradation} = \frac{\text{Sharpe}_{\text{OOS}}}{\text{Sharpe}_{\text{IS}}}$$
   - Strategies with severe drop-offs ($\text{Degradation} < 0.5$) are flagged for probable overfitting.

---

## 4. Performance & Risk Metrics Calculated

| Metric | Formula / Definition | Significance |
| :--- | :--- | :--- |
| **Total Return** | $\frac{V_{\text{final}} - V_{\text{initial}}}{V_{\text{initial}}} \times 100\%$ | Cumulative strategy gain. |
| **CAGR** | $(V_{\text{final}} / V_{\text{initial}})^{(365.25 / \text{Days})} - 1$ | Annualized compound rate of growth. |
| **Annualized Volatility** | $\sigma_{\text{daily}} \times \sqrt{252}$ | Total annualized price dispersion. |
| **Sharpe Ratio** | $\frac{\text{CAGR} - R_f}{\sigma_{\text{annual}}}$ | Excess return per unit of total risk. |
| **Sortino Ratio** | $\frac{\text{CAGR} - R_f}{\sigma_{\text{downside}}}$ | Excess return per unit of downside risk. |
| **Maximum Drawdown** | $\min_t \left(\frac{W_t - \max_{s \le t} W_s}{\max_{s \le t} W_s}\right)$ | Worst peak-to-trough decline. |
| **Calmar Ratio** | $\frac{\text{CAGR}}{\|\text{MDD}\|}$ | Return relative to drawdown risk. |
| **Win Rate** | $\frac{\text{Profitable Trades}}{\text{Total Trades}} \times 100\%$ | Proportion of winning trades. |
| **Profit Factor** | $\frac{\sum \text{Gains}}{\sum \|\text{Losses}\|}$ | Ratio of gross profits to gross losses. |

---

## 5. Supported Strategy Types

1. **SMA Crossover (`SMA_CROSSOVER`)**:
   - Long when Fast SMA crosses above Slow SMA.
   - Close / Cash when Fast SMA crosses below Slow SMA.
2. **RSI Mean Reversion (`RSI_MEAN_REVERSION`)**:
   - Long when 14-period Wilder RSI drops below Oversold threshold (e.g. 30).
   - Exit when RSI climbs above Overbought threshold (e.g. 70).
3. **Buy and Hold Benchmark (`BUY_AND_HOLD`)**:
   - Buys maximum shares on Day 1 Open and holds until series termination for direct alpha comparison.
