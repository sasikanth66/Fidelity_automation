# Complete Stock Scanner System - Quick Reference

## 🎯 What You Have

A complete support/resistance analysis and scanning system with:

1. **Support/Resistance Indicator** - Identifies key S&R zones
2. **Stock Scanner** - Finds stocks bouncing off S&R levels
3. **Visualizer** - Creates interactive charts

## 📁 Files Overview

```
support_resistance_indicator.py  # Core S&R calculation engine
sr_visualizer.py                 # Interactive chart creation
example_usage.py                 # NVDA 4H analysis example
stock_scanner.py                 # Scans stocks for bounces
visualize_scanner_results.py     # Quick chart generator
```

## 🚀 Quick Start Guide

### 1. Scan for Stocks Bouncing Off Support/Resistance

```bash
# Scan first 20 NASDAQ-100 stocks
python stock_scanner.py
```

**Output:**
- Terminal display of all stocks found
- CSV file with detailed results
- Identifies bullish (support) and bearish (resistance) setups

### 2. Visualize a Specific Stock

```bash
# After scanning, visualize any stock
python visualize_scanner_results.py NVDA
```

**Output:**
- Interactive HTML chart
- Shows all S&R zones, signals, and price action
- Opens in your browser

### 3. Analyze NVDA (Your Original Request)

```bash
# Run NVDA 4H analysis with 20-bar lookback
python example_usage.py
```

## 📊 Complete Workflow Example

```bash
# Step 1: Scan for opportunities
python stock_scanner.py

# Example output:
# ✅ NVDA - Support bounce at $480
# ✅ AMD - Support bounce at $138
# ✅ TSLA - Resistance bounce at $248

# Step 2: Visualize the promising ones
python visualize_scanner_results.py NVDA
python visualize_scanner_results.py AMD

# Step 3: Make trading decisions based on charts
```

## 🔍 Scanner Results Interpretation

### Support Bounces (Bullish Setups) 🟢

```
Symbol   Price      Support    Distance     Bars Ago   Strength
NVDA     $485.50    $480.00    +1.15%       1          🔥🔥
```

**What this means:**
- NVDA bounced off $480 support
- Currently at $485.50 (1.15% above support)
- Bounce happened 1 bar ago (very fresh!)
- Strong setup (🔥🔥)

**Trading idea:**
- Entry: Current price or pullback to $480
- Stop: Below $475 (below support zone)
- Target: Next resistance level

### Resistance Bounces (Bearish Setups) 🔴

```
Symbol   Price      Resistance   Distance     Bars Ago   Strength
TSLA     $242.50    $248.00      -2.22%       1          🔥🔥
```

**What this means:**
- TSLA rejected at $248 resistance
- Currently at $242.50 (2.22% below resistance)
- Rejection happened 1 bar ago
- Strong setup (🔥🔥)

**Trading idea:**
- Entry: Current price or rally to $248
- Stop: Above $252 (above resistance zone)
- Target: Next support level

## 🎨 Using the Visualizer

### From Command Line

```bash
# Visualize any stock
python visualize_scanner_results.py AAPL
python visualize_scanner_results.py MSFT
python visualize_scanner_results.py GOOGL
```

### From Python Script

```python
from visualize_scanner_results import visualize_stock, quick_viz

# Single stock
visualize_stock('NVDA')

# Multiple stocks from scan
stocks_to_check = ['NVDA', 'AMD', 'AAPL', 'MSFT']
quick_viz(stocks_to_check)
```

## ⚙️ Customization Examples

### Scan Different Timeframes

```python
from stock_scanner import SupportResistanceScanner

# Daily timeframe scan
scanner = SupportResistanceScanner(
    stocks=['NVDA', 'AMD', 'AAPL'],
    period="1y",
    interval="1d",
    timeframe="1D",      # Daily instead of 4H
    detection_length=15,
    lookback_bars=3
)
scanner.scan_all()
scanner.print_results()
```

### Scan Your Own Stocks

```python
from stock_scanner import quick_scan

# Your custom watchlist
my_stocks = [
    'NVDA', 'AMD', 'INTC',  # Semiconductors
    'AAPL', 'MSFT', 'GOOGL', # Big tech
    'TSLA', 'F', 'GM'        # Auto
]

scanner = quick_scan(stocks=my_stocks, lookback_bars=5)
```

### Change Lookback Period

```python
from stock_scanner import quick_scan

# More recent bounces (last 2 bars only)
scanner = quick_scan(lookback_bars=2)

# Wider window (last 5 bars)
scanner = quick_scan(lookback_bars=5)
```

## 📈 Parameters Guide

### Scanner Parameters

| Parameter | Recommended | Description |
|-----------|-------------|-------------|
| `lookback_bars=3` | 2-5 | How recent the bounce must be |
| `detection_length=20` | 15-25 | Pivot sensitivity (higher = stronger zones) |
| `timeframe="4H"` | 1H, 4H, 1D | Chart timeframe |
| `period="6mo"` | 3mo-1y | Historical data amount |
| `max_stocks=20` | 10-100 | How many stocks to scan |

### When to Adjust

**For Day Trading:**
- timeframe="1H"
- lookback_bars=2
- detection_length=15

**For Swing Trading (recommended):**
- timeframe="4H"
- lookback_bars=3
- detection_length=20

**For Position Trading:**
- timeframe="1D"
- lookback_bars=5
- detection_length=20

## 💡 Pro Tips

### 1. Run Scans Regularly
```bash
# Create a daily routine
# Morning: Scan for new setups
python stock_scanner.py

# Review CSV results
# Visualize top 3-5 setups
# Make trading plan
```

### 2. Focus on Fresh Bounces
- Prioritize `Bars_Ago = 0` or `1`
- These are happening RIGHT NOW

### 3. Check Multiple Timeframes
```python
# Check 4H for entry
quick_scan(timeframe="4H", lookback_bars=3)

# Verify on daily for trend
quick_scan(timeframe="1D", lookback_bars=5)
```

### 4. Filter by Distance
- Best entries: < 2% from zone
- Avoid: > 5% from zone (already moved too much)

### 5. Combine with Volume
- Look at the charts (visualizer)
- Higher volume on bounce = stronger signal

## 📊 Output Files

### CSV File Structure
```
Symbol,Type,Current_Price,Zone_Level,Distance_Pct,Bars_Ago,Touch_Price,Bounce_Close
NVDA,Support Bounce,485.50,480.00,1.15,1,478.20,482.50
AMD,Support Bounce,142.80,138.50,3.11,0,138.20,140.50
```

Import into Excel/Google Sheets for further analysis!

## 🎯 Real Trading Example

Let's say you run the scanner and get:

```
🟢 STOCKS BOUNCING OFF SUPPORT
NVDA     $485.50    $480.00    +1.15%       1          🔥🔥
```

**Step-by-step:**

1. **Verify the bounce**
   ```bash
   python visualize_scanner_results.py NVDA
   ```

2. **Check the chart**
   - Is support zone clean and tested?
   - Is there bullish volume on the bounce?
   - Are there manipulation zones (stop hunts)?

3. **Plan the trade**
   - Entry: $485-487 (current area)
   - Stop: $475 (below support)
   - Target: Next resistance (check chart)
   - Risk/Reward: Should be at least 1:2

4. **Execute**
   - Enter position
   - Set stop loss
   - Monitor on 4H chart

## 🔧 Troubleshooting

### "No bounces found"
- Try `lookback_bars=5` (wider window)
- Check if market is trending (no bounces)
- Scan more stocks (`max_stocks=50`)

### "Rate limiting errors"
```python
scanner.scan_all(delay=1.0)  # Increase delay
```

### "Chart doesn't open"
- Check the HTML file in folder
- Open manually in browser
- Make sure plotly is installed

### "Insufficient data"
- Stock might be newly listed
- Try shorter period: `period="3mo"`
- Some stocks have sparse data

## 📚 Additional Resources

- `SR_INDICATOR_README.md` - Detailed indicator documentation
- `SCANNER_README.md` - Complete scanner guide
- `example_usage.py` - Code examples

## 🎉 Quick Commands Cheat Sheet

```bash
# Scan stocks (top 20)
python stock_scanner.py

# Visualize a stock
python visualize_scanner_results.py NVDA

# Analyze NVDA specifically
python example_usage.py

# Full scan (all 100)
# Edit stock_scanner.py: max_stocks=None

# Custom stock list
# Edit stock_scanner.py: my_stocks = [...]
```

## 🚦 Next Steps

1. **Test the scanner**
   ```bash
   python stock_scanner.py
   ```

2. **Review results**
   - Check terminal output
   - Open CSV file

3. **Visualize top picks**
   ```bash
   python visualize_scanner_results.py SYMBOL
   ```

4. **Paper trade** the setups before going live

5. **Track performance** of scanner results over time

---

**You now have a professional-grade S&R scanning system!** 🎯

*Happy trading and remember to always manage your risk!*
