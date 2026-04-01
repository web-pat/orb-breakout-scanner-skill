# ORB Logic – Calculation Details

## 1. Calculate the Opening Range

The Opening Range (OR) is the **first fully closed 15-minute candle** after market open.

```
OR_HIGH  = Highest price of the 09:30–09:45 ET candle (including wicks)
OR_LOW   = Lowest price of the 09:30–09:45 ET candle (including wicks)
OR_WIDTH = OR_HIGH - OR_LOW
```

**Quality filter:**
- OR_WIDTH / OR_LOW < 0.05  → Acceptable (less than 5% width)
- OR_WIDTH / OR_LOW >= 0.05 → Warning "very wide range"

---

## 2. Confirmation Candle (5-Min Chart)

A confirmation is valid when a **5-minute candle closes entirely outside the OR**:

```
LONG confirmation:  candle LOW  > OR_HIGH  AND  candle CLOSE > OR_HIGH
SHORT confirmation: candle HIGH < OR_LOW   AND  candle CLOSE < OR_LOW
```

Partial breakouts (wick outside, body inside) do **not** count as confirmation.

---

## 3. Entry Scenarios (1-Min Chart)

### Scenario A – Breakout (Momentum / Fair Value Gap)
A Fair Value Gap (FVG) exists when the wicks of candle 1 and candle 3 **do not overlap**:

```
FVG_LONG:  Candle3_LOW  > Candle1_HIGH  → gap upward
FVG_SHORT: Candle3_HIGH < Candle1_LOW   → gap downward
```

**Entry:** at the close price of the middle candle (candle 2)
**SL:** below OR_HIGH (Long) / above OR_LOW (Short), distance = OR_WIDTH * 0.3

### Scenario B – Retest
Price breaks out but briefly pulls back to the outer edge of the box:

```
LONG  retest: after breakout price falls back to at most OR_HIGH * 1.002
SHORT retest: after breakout price rises back to at least OR_LOW  * 0.998
```

**Entry:** top (Long) / bottom (Short) of the next confirming green/red candle
**SL:** last 1-min low below OR_HIGH (Long) / last 1-min high above OR_LOW (Short)

### Scenario C – Reversal (Failed Breakout)
Price leaves the box but immediately returns inside:

```
LONG  reversal: price breaks SHORT side, re-enters box, then exceeds last local high
SHORT reversal: price breaks LONG  side, re-enters box, then falls below last local low
```

**Entry:** when the last counter-move high/low is broken
**SL:** extreme point of the failed breakout + small buffer (OR_WIDTH * 0.2)

---

## 4. Take Profit Calculation (2:1 RRR)

```
RISK = abs(ENTRY - STOP_LOSS)
TAKE_PROFIT_LONG  = ENTRY + (RISK * 2)
TAKE_PROFIT_SHORT = ENTRY - (RISK * 2)
```

---

## 5. Signal Ranking (Priority)

When multiple signals are present, rank by the following criteria:

1. **Volume:** breakout candle has higher volume than the last 5 candles → preferred
2. **Range width:** narrower Opening Range → more reliable breakout
3. **Time:** earlier confirmation (09:45–10:30 ET) → preferred over late signals
4. **Scenario:** Retest > Breakout > Reversal (by reliability)

---

## 6. Data Mapping (yfinance)

```python
# 1-minute data for the current day
df_1m = yf.download(ticker, period="1d", interval="1m", auto_adjust=True)

# 5-minute data for the current day
df_5m = yf.download(ticker, period="1d", interval="5m", auto_adjust=True)

# Columns: Open, High, Low, Close, Volume
# Index:   DatetimeIndex with timezone (UTC → convert to ET)
```

**Timezone conversion:**
```python
import pytz
ET = pytz.timezone("America/New_York")
df.index = df.index.tz_convert(ET)
```

**Filter Opening Range candle:**
```python
or_start = df_5m.index[df_5m.index.time == pd.Timestamp("09:30").time()]
or_candle = df_5m.loc[or_start[0]]  # first 09:30 candle
```
