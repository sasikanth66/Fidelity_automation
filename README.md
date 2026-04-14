# Stock Support & Resistance Scanner

A professional-grade Python system for identifying support and resistance levels and scanning stocks for trading opportunities.

## 🎯 What This Does

1. **Identifies Support & Resistance Zones** - Based on pivot points and price action
2. **Scans Multiple Stocks** - Finds stocks bouncing off S/R levels
3. **Generates Trading Signals** - Breakouts, tests, retests, and rejections
4. **Creates Interactive Charts** - Visualize S/R zones and price action

## 📁 Project Structure

```
stock_sr_scanner/
├── README.md                           # This file
├── QUICK_START.md                      # Quick reference guide
├── SR_INDICATOR_README.md              # Detailed indicator documentation
├── SCANNER_README.md                   # Complete scanner guide
├── requirements.txt                    # Python dependencies
│
├── support_resistance_indicator.py     # Core S&R calculation engine
├── sr_visualizer.py                    # Interactive chart creator
├── example_usage.py                    # NVDA 4H analysis example
├── stock_scanner.py                    # Multi-stock scanner
├── visualize_scanner_results.py        # Quick chart generator
└── demo_scanner.py                     # Demo with sample data
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd stock_sr_scanner
pip install -r requirements.txt
```

### 2. Run Demo (Works Offline)

```bash
python demo_scanner.py
```

### 3. Scan Real Stocks (Requires Internet)

```bash
python stock_scanner.py
```

### 4. Visualize a Stock

```bash
python visualize_scanner_results.py NVDA
```

### 5. Analyze NVDA Specifically

```bash
python example_usage.py
```

## 📊 Example Output

### Scanner Results

```
🟢 STOCKS BOUNCING OFF SUPPORT (BULLISH SETUPS)
Symbol   Price      Support    Distance     Bars Ago   Strength
NVDA     $485.50    $480.00    +1.15%       1          🔥🔥
META     $300.55    $297.36    +1.07%       1          🔥🔥
AMD      $142.80    $138.50    +3.11%       0          🔥🔥🔥

🔴 STOCKS BOUNCING OFF RESISTANCE (BEARISH SETUPS)
Symbol   Price      Resistance   Distance     Bars Ago   Strength
TSLA     $242.50    $248.00      -2.22%       1          🔥🔥
```

### Chart Output

Interactive HTML charts with:
- Candlestick price action
- Support/resistance zones (shaded areas)
- Trading signals (markers)
- Volume analysis
- Manipulation zones

## 📚 Documentation

- **[QUICK_START.md](QUICK_START.md)** - Quick reference and examples
- **[SR_INDICATOR_README.md](SR_INDICATOR_README.md)** - Indicator details
- **[SCANNER_README.md](SCANNER_README.md)** - Scanner guide

## 🎯 Main Use Cases

### 1. Daily Stock Scanning
```bash
python stock_scanner.py
# Finds stocks bouncing off support/resistance
# Exports results to CSV
```

### 2. Analyze Specific Stock
```bash
python visualize_scanner_results.py AAPL
# Creates interactive chart
# Shows all S&R zones
```

### 3. Custom Analysis
```python
from support_resistance_indicator import SupportResistanceIndicator
from sr_visualizer import SRVisualizer
import yfinance as yf

# Download data
df = yf.Ticker("NVDA").history(period="6mo", interval="1h")
df.columns = df.columns.str.lower()

# Resample to 4H
df_4h = df.resample('4H').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
}).dropna()

# Calculate S&R
indicator = SupportResistanceIndicator(detection_length=20)
df_signals = indicator.calculate(df_4h)

# Visualize
visualizer = SRVisualizer(indicator)
fig = visualizer.plot(df_signals)
visualizer.show(fig)
```

## ⚙️ Configuration

### Scanner Parameters

```python
from stock_scanner import SupportResistanceScanner

scanner = SupportResistanceScanner(
    stocks=['NVDA', 'AMD', 'AAPL'],  # Stock list
    period="6mo",                     # Historical data period
    interval="1h",                    # Download interval
    timeframe="4H",                   # Chart timeframe
    detection_length=20,              # Pivot lookback
    lookback_bars=3                   # Bounce detection window
)

scanner.scan_all()
scanner.print_results()
```

### Indicator Parameters

```python
from support_resistance_indicator import SupportResistanceIndicator

indicator = SupportResistanceIndicator(
    detection_length=20,          # Pivot detection length
    sr_margin=2.0,                # S&R zone width
    mn_margin=1.3,                # Manipulation zone width
    avoid_false_breakouts=True,   # Filter false breakouts
    check_historical_sr=True,     # Check previous zones
    show_manipulation=True        # Show liquidity sweeps
)
```

## 🎨 Features

### Support & Resistance Detection
✅ Pivot-based zone identification
✅ Dynamic zone sizing based on volatility
✅ Historical level tracking
✅ Manipulation zone detection

### Trading Signals
✅ Breakouts (bullish/bearish)
✅ Tests (price touches zone)
✅ Retests (flipped zones)
✅ Rejections (long wicks + volume)
✅ Swing highs/lows

### Stock Scanner
✅ Multi-stock analysis
✅ Support bounce detection (bullish setups)
✅ Resistance bounce detection (bearish setups)
✅ Freshness scoring (bars ago)
✅ CSV export

### Visualization
✅ Interactive Plotly charts
✅ Candlestick with zones
✅ Volume subplot
✅ Signal markers
✅ HTML export

## 📈 Trading Workflow

1. **Morning**: Run scanner
   ```bash
   python stock_scanner.py
   ```

2. **Review**: Check terminal output and CSV

3. **Verify**: Visualize top setups
   ```bash
   python visualize_scanner_results.py NVDA
   ```

4. **Trade**: Execute with proper risk management

5. **Monitor**: Track on 4H timeframe

## 🔍 Scanner Interpretation

### Support Bounces (Bullish) 🟢
- **Entry**: Buy on confirmation above support
- **Stop**: Below support zone
- **Target**: Next resistance level
- **Best**: Distance < 2%, Bars_Ago = 0-1

### Resistance Bounces (Bearish) 🔴
- **Entry**: Short on confirmation below resistance
- **Stop**: Above resistance zone
- **Target**: Next support level
- **Best**: Distance < 2%, Bars_Ago = 0-1

## 🛠️ Customization Examples

### Different Timeframes
```python
# Daily timeframe
scanner = SupportResistanceScanner(
    timeframe="1D",
    detection_length=15
)

# Hourly timeframe
scanner = SupportResistanceScanner(
    timeframe="1H",
    detection_length=25
)
```

### Custom Stock Lists
```python
# Tech stocks
tech_stocks = ['NVDA', 'AMD', 'INTC', 'TSM', 'AVGO']

# FAANG
faang = ['META', 'AAPL', 'AMZN', 'NFLX', 'GOOGL']

# Run scanner
from stock_scanner import quick_scan
scanner = quick_scan(stocks=tech_stocks)
```

### Adjust Sensitivity
```python
# More sensitive (more signals)
indicator = SupportResistanceIndicator(
    detection_length=15,  # Shorter = more pivots
    sr_margin=1.5,        # Tighter zones
)

# Less sensitive (stronger signals)
indicator = SupportResistanceIndicator(
    detection_length=25,  # Longer = fewer pivots
    sr_margin=3.0,        # Wider zones
)
```

## 🐛 Troubleshooting

### Network Issues
If Yahoo Finance is blocked, use the demo:
```bash
python demo_scanner.py
```

### No Bounces Found
- Increase `lookback_bars` (5-10)
- Scan more stocks (`max_stocks=50`)
- Adjust `detection_length`

### Too Many Signals
- Decrease `lookback_bars` (1-2)
- Increase `detection_length` (25-30)
- Filter by distance in results

## 📦 Requirements

- Python 3.8+
- pandas
- numpy
- plotly
- yfinance (for live data)

## 🎓 Learning Resources

### Read First
1. **QUICK_START.md** - Get up and running
2. **SCANNER_README.md** - Understand the scanner
3. **SR_INDICATOR_README.md** - Learn the indicator

### Example Scripts
- `example_usage.py` - NVDA analysis
- `demo_scanner.py` - Sample data demo
- `visualize_scanner_results.py` - Chart creation

## 📝 License

This is a translation of the LuxAlgo Support and Resistance Signals MTF indicator from Pine Script to Python.

Original indicator: © LuxAlgo
Licensed under CC BY-NC-SA 4.0
https://creativecommons.org/licenses/by-nc-sa/4.0/

## 🙏 Credits

- Original Pine Script indicator by **LuxAlgo**
- Python translation maintains core logic and algorithms

## 🚀 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Run demo**: `python demo_scanner.py`
3. **Try scanner**: `python stock_scanner.py`
4. **Read docs**: Check QUICK_START.md

---

**Happy Trading!** 📈

*This tool identifies setups, not guaranteed trades. Always verify charts and manage risk properly.*
