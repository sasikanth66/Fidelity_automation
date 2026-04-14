# Stock Scanner for Support/Resistance Bounces

## Quick Start

### Basic Usage (Scan Top 20 NASDAQ-100 Stocks)

```bash
python stock_scanner.py
```

This will scan the first 20 NASDAQ-100 stocks and identify ones that bounced off support or resistance in the last 3 bars.

### Example Output

```
================================================================================
SCANNING 20 STOCKS FOR SUPPORT/RESISTANCE BOUNCES
================================================================================

Parameters:
  - Timeframe: 4H
  - Detection Length: 20
  - Lookback Bars: 3
  - Period: 6mo

================================================================================

[1/20] Scanning AAPL... ✅ SUPPORT BOUNCE ($175.50)
[2/20] Scanning MSFT... ⚪ No bounce
[3/20] Scanning GOOGL... ✅ RESISTANCE BOUNCE ($142.80)
...

================================================================================
🟢 STOCKS BOUNCING OFF SUPPORT (BULLISH SETUPS)
================================================================================

Found 5 stocks:

Symbol   Price      Support    Distance     Bars Ago   Strength
----------------------------------------------------------------------------------------------------
NVDA     $485.50    $480.00    +1.15%       1          🔥🔥
AAPL     $178.20    $175.50    +1.54%       2          🔥
AMD      $142.80    $138.50    +3.11%       0          🔥🔥🔥

================================================================================
🔴 STOCKS BOUNCING OFF RESISTANCE (BEARISH SETUPS)
================================================================================

Found 3 stocks:

Symbol   Price      Resistance   Distance     Bars Ago   Strength
----------------------------------------------------------------------------------------------------
TSLA     $242.50    $248.00      -2.22%       1          🔥🔥
```

## Usage Examples

### 1. Quick Scan (First 20 Stocks)

```python
from stock_scanner import quick_scan

# Scan first 20 NASDAQ-100 stocks
scanner = quick_scan(max_stocks=20, lookback_bars=3)
```

### 2. Full NASDAQ-100 Scan

```python
from stock_scanner import quick_scan

# Scan all ~100 stocks (takes 1-2 minutes)
scanner = quick_scan(max_stocks=None, lookback_bars=3)
```

### 3. Custom Stock List

```python
from stock_scanner import quick_scan

# Scan your own list
my_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMD', 'META']
scanner = quick_scan(stocks=my_stocks, lookback_bars=3)
```

### 4. Advanced Custom Scan

```python
from stock_scanner import SupportResistanceScanner

# Create custom scanner
scanner = SupportResistanceScanner(
    stocks=['NVDA', 'AMD', 'AVGO'],
    period="6mo",           # Data period
    interval="1h",          # Download interval
    timeframe="4H",         # Resample to 4H
    detection_length=20,    # Lookback for pivots
    lookback_bars=5         # Check last 5 bars for bounces
)

# Run scan
scanner.scan_all(delay=0.5)
scanner.print_results()
scanner.export_to_csv("my_scan.csv")
```

## Parameters

### Scanner Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `stocks` | NASDAQ-100 | List of stock symbols to scan |
| `period` | "6mo" | Historical data period |
| `interval` | "1h" | Download interval (1h, 1d, etc.) |
| `timeframe` | "4H" | Resampled timeframe |
| `detection_length` | 20 | Lookback for pivot detection |
| `lookback_bars` | 3 | Recent bars to check for bounces |

### Bounce Detection Logic

**Support Bounce (Bullish):**
1. Price touches/goes below support zone in last N bars
2. Price closes ABOVE support (bounce)
3. Subsequent bars show bullish follow-through

**Resistance Bounce (Bearish):**
1. Price touches/goes above resistance zone in last N bars
2. Price closes BELOW resistance (rejection)
3. Subsequent bars show bearish follow-through

## Output Files

### CSV Export
Automatically exports results to CSV with timestamp:
- `bounce_scan_YYYYMMDD_HHMMSS.csv`

### Columns
- Symbol
- Type (Support Bounce / Resistance Bounce)
- Current_Price
- Zone_Level
- Distance_Pct (how far from zone)
- Bars_Ago (when bounce occurred)
- Touch_Price
- Bounce_Close

## Strength Indicators

- 🔥🔥🔥 = Bounce happened on current bar (0 bars ago)
- 🔥🔥 = Bounce happened 1 bar ago
- 🔥 = Bounce happened 2-3 bars ago

## Interpreting Results

### Support Bounces (Bullish Setups)
- **Entry**: Buy on confirmation (current bar close above support)
- **Stop Loss**: Below support zone
- **Target**: Next resistance zone
- **Best Setup**: Distance < 2% and Bars_Ago = 0-1

### Resistance Bounces (Bearish Setups)
- **Entry**: Short on confirmation (current bar close below resistance)
- **Stop Loss**: Above resistance zone
- **Target**: Next support zone
- **Best Setup**: Distance < 2% and Bars_Ago = 0-1

## Tips for Best Results

### 1. Focus on Fresh Bounces
- Prioritize stocks with `Bars_Ago = 0` or `1`
- These are the most recent setups

### 2. Check Distance
- Stocks closest to the zone (`Distance_Pct` near 0%) are ideal
- Avoid stocks that have moved too far already

### 3. Verify Manually
- Always check the chart before trading
- Use the original `example_usage.py` to visualize:

```python
from support_resistance_indicator import SupportResistanceIndicator
from sr_visualizer import SRVisualizer
import yfinance as yf

# Visualize a specific stock from scan results
df = yf.Ticker("NVDA").history(period="6mo", interval="1h")
df.columns = df.columns.str.lower()
df_4h = df.resample('4H').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()

indicator = SupportResistanceIndicator(detection_length=20)
df_signals = indicator.calculate(df_4h)

visualizer = SRVisualizer(indicator)
fig = visualizer.plot(df_signals, title="NVDA Bounce Analysis")
visualizer.show(fig)
```

### 4. Run Regularly
- Scan daily or after market close
- Track which stocks appear repeatedly

### 5. Combine with Volume
- Higher volume on bounce = stronger signal
- Check the charts for volume confirmation

## Performance Tips

### Speed Up Scans
- Use `max_stocks` parameter to limit scan
- Increase `delay` if getting rate limited
- Download data once and reuse

### Reduce False Signals
- Increase `detection_length` (20-25) for stronger zones
- Require more `lookback_bars` for confirmation
- Filter by distance percentage

## NASDAQ-100 Stock List

The scanner includes ~100 major NASDAQ stocks:
- AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, etc.
- Tech: AMD, INTC, QCOM, TXN, etc.
- Healthcare: GILD, REGN, BIIB, etc.
- Consumer: SBUX, COST, ROST, etc.

Full list in `stock_scanner.py` - easily customizable!

## Troubleshooting

**No bounces found:**
- Try increasing `lookback_bars` (5-10)
- Market might be trending without bounces
- Adjust `detection_length`

**Too many results:**
- Decrease `lookback_bars` (1-2)
- Filter by `distance_pct` in results
- Increase `detection_length` for stronger zones

**Rate limiting errors:**
- Increase `delay` parameter (1.0-2.0 seconds)
- Scan fewer stocks at a time
- Use longer intervals between scans

## Example Workflow

```bash
# 1. Run scan
python stock_scanner.py

# 2. Review results in terminal

# 3. Check CSV file for details
# Opens: bounce_scan_20260106_143052.csv

# 4. Visualize promising setups
# Use example_usage.py modified for specific stock

# 5. Make trading decisions
# Based on chart confirmation and risk/reward
```

## Integration with Trading

### Watchlist Creation
```python
# Get symbols with fresh bounces
scanner = quick_scan(max_stocks=50, lookback_bars=2)

# Extract symbols
bullish_setups = [r['symbol'] for r in scanner.results['support_bounces']
                  if r['support_info']['bars_ago'] <= 1]

print("Add to bullish watchlist:", bullish_setups)
```

### Alert System
```python
# Monitor specific stocks
my_watchlist = ['NVDA', 'AMD', 'AAPL', 'MSFT']
scanner = quick_scan(stocks=my_watchlist, lookback_bars=1)

# Send alerts (implement your preferred method)
if scanner.results['support_bounces']:
    print("🚨 ALERT: New support bounces!")
```

---

**Happy scanning!** 📈

*Remember: This tool identifies setups, not guaranteed trades. Always verify charts and manage risk properly.*
