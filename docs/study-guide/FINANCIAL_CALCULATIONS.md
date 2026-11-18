# Financial Calculations, Mathematical Models & Reference Derivations

This document provides exact mathematical formulas, Python implementation details, numerical edge-case safeguards, and worked numerical examples for every quantitative metric used in **QuantWeave**.

---

## 1. Returns & Compounding

### Simple Return ($R_t$)
Measures the percentage price change over a single period:
$$R_t = \frac{P_t - P_{t-1}}{P_{t-1}}$$

### Logarithmic Return ($r_t$)
Continuous, time-additive returns used in quantitative modeling:
$$r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) = \ln(P_t) - \ln(P_{t-1})$$

### Compound Annual Growth Rate (CAGR)
Annualized geometric growth rate of an investment over multiple years:
$$\text{CAGR} = \left(\frac{V_{\text{final}}}{V_{\text{initial}}}\right)^{\frac{365}{\text{days}}} - 1$$

#### Mathematical Edge Cases & Safeguards
- **Days Guard**: If holding duration $< 365$ days, annualizing returns introduces severe distortion (e.g., 5% over 10 days $\implies$ 500%+ annualized). QuantWeave suppresses CAGR calculation when $\text{days} < 365$ and displays absolute simple return instead.
- **Negative Final Value**: If $V_{\text{final}} \le 0$ (bankruptcy or complete wipeout), CAGR is undefined and clamped to $-100\%$.

---

## 2. Moving Averages

### Simple Moving Average (SMA)
Unweighted mean of the last $N$ closing prices:
$$\text{SMA}_t = \frac{1}{N} \sum_{i=0}^{N-1} P_{t-i}$$

### Exponential Moving Average (EMA)
Weighted average placing exponentially greater weight on recent prices:
$$\text{EMA}_t = \alpha \cdot P_t + (1 - \alpha) \cdot \text{EMA}_{t-1}$$
$$\alpha = \frac{2}{N + 1}$$

- **Initialization**: $\text{EMA}_0 = \frac{1}{N} \sum_{i=0}^{N-1} P_i$ (initial seed uses SMA).

---

## 3. Relative Strength Index (RSI) with Wilder's Smoothing

Developed by J. Welles Wilder, RSI measures the magnitude of recent gains against recent losses on a 0–100 scale:

$$U_t = \max(P_t - P_{t-1}, 0)$$
$$D_t = \max(P_{t-1} - P_t, 0)$$

### Wilder's Smoothing Formulation
Unlike standard EMA ($\alpha = 2/(N+1)$), Wilder's smoothing uses $\alpha = 1/N$:
$$\text{AvgGain}_t = \frac{\text{AvgGain}_{t-1} \cdot (N - 1) + U_t}{N}$$
$$\text{AvgLoss}_t = \frac{\text{AvgLoss}_{t-1} \cdot (N - 1) + D_t}{N}$$

$$\text{RS} = \frac{\text{AvgGain}_t}{\text{AvgLoss}_t}$$
$$\text{RSI} = 100 - \frac{100}{1 + \text{RS}} = 100 \cdot \frac{\text{AvgGain}_t}{\text{AvgGain}_t + \text{AvgLoss}_t}$$

### Edge Case Safeguards
1. **Flat Prices ($\text{AvgGain} = 0 \text{ and } \text{AvgLoss} = 0$)**: If an instrument's price does not move across 14 consecutive sessions, $\text{RS}$ is undefined ($0/0$). QuantWeave clamps $\text{RSI} = 50.0$ (neutral).
2. **Zero Loss ($\text{AvgLoss} = 0$)**: If price rises every session, $\text{RSI} = 100.0$.
3. **Zero Gain ($\text{AvgGain} = 0$)**: If price drops every session, $\text{RSI} = 0.0$.

---

## 4. MACD & Bollinger Bands

### Moving Average Convergence Divergence (MACD)
$$\text{MACD Line} = \text{EMA}_{12}(P) - \text{EMA}_{26}(P)$$
$$\text{Signal Line} = \text{EMA}_9(\text{MACD Line})$$
$$\text{Histogram} = \text{MACD Line} - \text{Signal Line}$$

### Bollinger Bands
Measures price volatility around a 20-period moving average:
$$\text{Middle Band} = \text{SMA}_{20}(P)$$
$$\sigma_{20} = \sqrt{\frac{1}{20}\sum_{i=0}^{19} (P_{t-i} - \text{Middle Band})^2}$$
$$\text{Upper Band} = \text{Middle Band} + 2 \cdot \sigma_{20}$$
$$\text{Lower Band} = \text{Middle Band} - 2 \cdot \sigma_{20}$$

---

## 5. Risk-Adjusted Return Metrics

### Annualized Volatility ($\sigma_{\text{ann}}$)
Standard deviation of daily log returns annualized across 252 trading days:
$$\sigma_{\text{ann}} = \sqrt{\frac{1}{T-1} \sum_{t=1}^T (r_t - \bar{r})^2} \times \sqrt{252}$$

### Sharpe Ratio
Excess annualized return per unit of total risk:
$$\text{Sharpe} = \frac{R_p - R_f}{\sigma_p}$$
- Default risk-free rate ($R_f$): $6.5\%$ (91-day Government of India T-Bill rate).

### Sortino Ratio
Excess annualized return per unit of **downside** risk (ignores upside volatility):
$$\text{Sortino} = \frac{R_p - R_f}{\sigma_d}$$
$$\sigma_d = \sqrt{\frac{1}{T} \sum_{t=1}^T \min(r_t - \tau, 0)^2} \times \sqrt{252}$$
- Where $\tau = R_f / 252$ is the daily minimum acceptable return.

### Maximum Drawdown (MDD)
The maximum peak-to-trough decline before a new peak is achieved:
$$\text{Peak}_t = \max_{0 \le \tau \le t} (V_\tau)$$
$$\text{Drawdown}_t = \frac{V_t - \text{Peak}_t}{\text{Peak}_t}$$
$$\text{MDD} = \min_{0 \le t \le T} (\text{Drawdown}_t)$$

---

## 6. Portfolio Ledger Accounting & Cost Basis

### Weighted-Average Cost Basis (WACB)
When acquiring shares at different price points, the cost basis is the weighted average purchase price:
$$\text{WACB}_{\text{new}} = \frac{(\text{Shares}_{\text{existing}} \cdot \text{WACB}_{\text{existing}}) + (\text{Shares}_{\text{buy}} \cdot P_{\text{buy}})}{\text{Shares}_{\text{existing}} + \text{Shares}_{\text{buy}}}$$

### Realized Profit & Loss (P&L)
Realized on a SELL transaction:
$$\text{Realized P\&L} = \text{Shares}_{\text{sold}} \cdot (P_{\text{sell}} - \text{WACB}_{\text{current}})$$

### Unrealized Profit & Loss (P&L)
Paper profit on remaining open positions:
$$\text{Unrealized P\&L} = \text{Shares}_{\text{held}} \cdot (P_{\text{current}} - \text{WACB}_{\text{current}})$$

#### Worked Example
1. Day 1: BUY 100 shares of INFOSYS at ₹1,400.
   - Cost Basis = ₹1,400. Total Cost = ₹140,000.
2. Day 2: BUY 50 shares of INFOSYS at ₹1,550.
   - New WACB = $\frac{(100 \times 1,400) + (50 \times 1,550)}{150} = \frac{140,000 + 77,500}{150} = \frac{217,500}{150} =$ **₹1,450.00**.
3. Day 3: SELL 60 shares at ₹1,600.
   - Realized P&L = $60 \times (1,600 - 1,450) = 60 \times 150 =$ **₹9,000.00**.
   - Remaining shares = 90. WACB remains unchanged at **₹1,450.00**.

---

## 7. Performance Solvers: TWR vs XIRR

### Time-Weighted Return (TWR)
Eliminates the distorting effect of cash inflows and outflows:
$$\text{TWR} = \prod_{i=1}^M (1 + R_i) - 1$$
Where $R_i = \frac{V_i - (V_{i-1} + C_i)}{V_{i-1} + C_i}$ for sub-period $i$.

### Extended Internal Rate of Return (XIRR)
Annualized rate of return solving the Net Present Value equation for irregular cash flows $(C_i, t_i)$:
$$\text{NPV}(r) = \sum_{i=1}^n \frac{C_i}{(1 + r)^{\frac{t_i - t_0}{365}}} = 0$$

#### Newton-Raphson Solver with Bisection Fallback
In `apps/api/app/services/portfolio_service.py`:
$$r_{k+1} = r_k - \frac{\text{NPV}(r_k)}{\text{NPV}'(r_k)}$$
$$\text{NPV}'(r) = -\sum_{i=1}^n \frac{C_i \cdot \frac{t_i - t_0}{365}}{(1 + r)^{\frac{t_i - t_0}{365} + 1}}$$

- If Newton-Raphson fails to converge within 50 iterations (due to inflection points in derivative $\text{NPV}'$), QuantWeave automatically falls back to **Bisection Search** over bracket $[-0.99, 10.0]$ to guarantee finding the unique financial root.

---

## 8. Mutual Fund Analytics & Systematic Investment Plans (SIP)

### Net Asset Value (NAV)
$$\text{NAV} = \frac{\text{Total Fund Assets} - \text{Total Fund Liabilities}}{\text{Total Outstanding Units}}$$

### Future Value of Systematic Investment Plan (SIP)
Calculates projected corpus for monthly deposits $P$ over $n$ months at monthly interest rate $i = r / 12$:
$$M = P \times \left[ \frac{(1 + i)^n - 1}{i} \right] \times (1 + i)$$

#### Worked Example
- Monthly Investment $P = ₹10,000$
- Expected Annual Return $r = 12\%$ ($i = 0.12 / 12 = 0.01$)
- Tenure = 10 Years ($n = 120$ months)

$$M = 10,000 \times \left[ \frac{(1.01)^{120} - 1}{0.01} \right] \times 1.01$$
$$(1.01)^{120} \approx 3.30039$$
$$M = 10,000 \times \frac{2.30039}{0.01} \times 1.01 = 10,000 \times 230.039 \times 1.01 \approx \mathbf{₹2,323,394}$$
- Total Invested Amount: $120 \times 10,000 = \mathbf{₹1,200,000}$
- Estimated Wealth Gain: $2,323,394 - 1,200,000 = \mathbf{₹1,123,394}$
