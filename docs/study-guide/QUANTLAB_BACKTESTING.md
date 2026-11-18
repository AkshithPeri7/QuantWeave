# QuantLab — Algorithmic Simulation & Lookahead-Free Backtesting

QuantLab is **QuantWeave's** institutional algorithmic trading simulation engine. This guide explains the mechanics of historical backtesting, how QuantLab prevents look-ahead bias, models transaction friction, and avoids overfitting.

---

## 1. Look-Ahead Bias & The Backtesting Fallacy

The most common flaw in amateur algorithmic backtesting is **look-ahead bias** (information leakage from future timestamps).

### The Flawed "Same-Bar" Execution Model
Consider an SMA crossover strategy:
1. At 15:30 (Market Close) of Day $t$, the Close price is finalized.
2. The algorithm calculates: `SMA_Fast(t) > SMA_Slow(t)` $\implies$ BUY Signal!
3. **Flaw**: The engine fills the buy order at Day $t$'s Close price $P_t$.
4. **Why this fails**: In live trading, you cannot know that the Close price completed the crossover until after the market has already closed! You cannot execute a trade at a price that occurred before or simultaneously with the signal generation.

### QuantLab's Lookahead-Free Solution: Next-Bar Open Execution
QuantLab strictly enforces sequential causality:
- **Signal Bar ($t$)**: At bar $t$'s Close, the strategy evaluates market conditions and generates a target action (`BUY`, `SELL`, `HOLD`).
- **Execution Bar ($t+1$)**: The trade order is routed to the simulated broker and filled at the **Open price of the next trading session ($P_{t+1}^{\text{open}}$)**.

```
Time ────────────────────────────────────────────────────────►
Day t:
  [ Open ] ───────── [ High ] ───────── [ Low ] ───────── [ Close ]
                                                            │
                                                            ▼ (Calculate Signal: BUY)
Day t+1:
  [ Open ] ◄── FILL ORDER HERE (with slippage & fees)
    │
    ▼
  [ High ] ───────── [ Low ] ───────── [ Close ]
```

---

## 2. Friction Modeling: Slippage & Transaction Costs

In paper simulations, assuming zero-friction execution leads to massively inflated returns. QuantLab implements two real-world friction models in `apps/api/app/services/quantlab_engine.py`:

### Slippage Model
Slippage accounts for bid-ask spread and market impact:
- **BUY Order**: Executed above the Open price:
  $$P_{\text{fill}} = P_{t+1}^{\text{open}} \times (1 + \text{slippage\_pct})$$
- **SELL Order**: Executed below the Open price:
  $$P_{\text{fill}} = P_{t+1}^{\text{open}} \times (1 - \text{slippage\_pct})$$
- Default slippage: `0.05%` (5 basis points).

### Transaction Fees & Exchange Levies
Every transaction incurs broker commissions, STT (Securities Transaction Tax), exchange turnover fees, and GST:
$$\text{Fee} = \text{Amount} \times \text{fee\_pct}$$
$$\text{Total Cost (BUY)} = (\text{Shares} \times P_{\text{fill}}) + \text{Fee}$$
$$\text{Net Proceeds (SELL)} = (\text{Shares} \times P_{\text{fill}}) - \text{Fee}$$
- Default fee: `0.10%` (10 basis points).

---

## 3. Position Accounting & Long-Only Safeguards

QuantLab implements a cash-isolated, long-only portfolio accounting simulator:

### Capital Allocation Rules
- Maximum capital committed per trade: User-defined percentage (default: `95%` of current cash balance, reserving `5%` buffer for slippage and transaction costs).
- Fractional Shares: Disallowed; shares are integer truncated `math.floor(target_cash / fill_price)`.
- Cash Balance Non-Negativity: Cash can never drop below zero. If fees or price gaps exceed buffer, order size is scaled down dynamically.

---

## 4. Train / Test Split & Overfitting Prevention

Strategy parameters optimized solely on historical backtests inevitably fit to historical noise rather than genuine predictive patterns (curve fitting).

### Out-of-Sample Validation
QuantLab allows partitioning historical data into **In-Sample (Train)** and **Out-of-Sample (Test)** intervals:
- **In-Sample (70%)**: Parameter optimization (e.g., finding the best Fast/Slow SMA window via Grid Search).
- **Out-of-Sample (30%)**: Unseen data evaluated with the optimized parameters to measure real performance degradation.

```
Historical Dataset (e.g., 2020 - 2026)
├───────────────────────────────────────┼───────────────────────┤
│        In-Sample Training (70%)       │  Out-of-Sample (30%)  │
│        (Parameter Optimization)       │ (Validation Baseline) │
```

### Overfitting Warning Signs
- **Sharpe Ratio Collapse**: If In-Sample Sharpe is $2.4$, but Out-of-Sample Sharpe drops to $0.3$, the strategy is overfitted.
- **Excessive Parameter Sensitivity**: If SMA(19, 49) yields +80% return, but SMA(20, 50) yields -10%, the strategy relies on spurious historical data points rather than robust trend-following.

---

## 5. Grid Search Optimization Engine

In `apps/api/app/services/quantlab_engine.py`, QuantLab provides a multi-parameter grid search optimizer:

```python
def run_grid_search(
    strategy_type: str,
    prices: list[DailyPrice],
    param_grid: dict[str, list[Any]],
    max_combinations: int = 100
) -> list[OptimizationResult]:
    """Generates the Cartesian product of parameter ranges and evaluates each.
    
    Guarded by max_combinations to prevent server denial-of-service.
    """
    keys, values = zip(*param_grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    if len(combinations) > max_combinations:
        raise ValueError(f"Grid search exceeds maximum combination limit of {max_combinations}")
        
    results = []
    for params in combinations:
        metrics = execute_simulation(strategy_type, prices, params)
        results.append(OptimizationResult(params=params, metrics=metrics))
        
    return sorted(results, key=lambda x: x.metrics.sharpe_ratio, reverse=True)
```
