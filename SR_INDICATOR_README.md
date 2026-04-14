# Support and Resistance Signals MTF - Python

Python translation of the LuxAlgo Support and Resistance Signals Multi-Timeframe (MTF) indicator from Pine Script v5.

## Overview

This indicator identifies support and resistance zones based on pivot points and generates various trading signals including:

- **Breakouts**: Price breaks through support/resistance levels
- **Tests**: Price touches but doesn't break through levels
- **Retests**: Price returns to test a flipped level after breakout
- **Rejections**: Price rejection patterns with long wicks and high volume
- **Manipulation Zones**: Liquidity sweeps and stop hunts
- **Swing Highs/Lows**: Key pivot points

## Installation

```bash
pip install pandas numpy plotly yfinance
```

## Required Dependencies

- `pandas`: Data manipulation
- `numpy`: Numerical calculations
- `plotly`: Interactive visualizations
- `yfinance`: Download market data (optional, for examples)

## Files

- `support_resistance_indicator.py`: Main indicator class
- `sr_visualizer.py`: Visualization module using Plotly
- `example_usage.py`: Usage examples and demonstrations

## Quick Start

### Basic Usage

```python
import pandas as pd
from support_resistance_indicator import SupportResistanceIndicator
from sr_visualizer import SRVisualizer
import yfinance as yf

# Download sample data
df = yf.Ticker("AAPL").history(period="6mo", interval="1d")
df.columns = df.columns.str.lower()
df = df[['open', 'high', 'low', 'close', 'volume']]

# Create indicator
indicator = SupportResistanceIndicator(
    detection_length=15,
    sr_margin=2.0,
    mn_margin=1.3,
    avoid_false_breakouts=True,
    check_historical_sr=True,
    show_manipulation=True
)

# Calculate signals
df_with_signals = indicator.calculate(df)

# Visualize
visualizer = SRVisualizer(indicator)
fig = visualizer.plot(df_with_signals, title="AAPL Support & Resistance")
visualizer.show(fig)
```

### Using Your Own Data

```python
# Load from CSV
df = pd.read_csv('your_data.csv')
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# Must have columns: open, high, low, close, volume
df = df[['open', 'high', 'low', 'close', 'volume']]

# Calculate
indicator = SupportResistanceIndicator()
df_with_signals = indicator.calculate(df)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `detection_length` | int | 15 | Length for pivot point detection |
| `sr_margin` | float | 2.0 | Support/Resistance zone margin multiplier |
| `mn_margin` | float | 1.3 | Manipulation zone margin multiplier |
| `avoid_false_breakouts` | bool | True | Filter breakouts that fail to continue |
| `check_historical_sr` | bool | True | Check previous historical S&R zones |
| `show_manipulation` | bool | True | Show manipulation zones |

## Signal Columns

After calling `indicator.calculate(df)`, the following boolean columns are added:

- `breakout_bullish`: Bullish breakout detected
- `breakout_bearish`: Bearish breakout detected
- `test_bullish`: Test of support zone
- `test_bearish`: Test of resistance zone
- `retest_bullish`: Retest of support after breakout
- `retest_bearish`: Retest of resistance after breakout
- `rejection_bullish`: Rejection of lower prices (long lower shadow + high volume)
- `rejection_bearish`: Rejection of higher prices (long upper shadow + high volume)
- `swing_high`: Swing high detected
- `swing_low`: Swing low detected

Each signal also has a corresponding `_price` column (e.g., `breakout_bullish_price`).

## Examples

The `example_usage.py` file contains several examples:

1. **Basic Usage**: Default settings with AAPL data
2. **Custom Settings**: Adjusted parameters for volatile markets (BTC)
3. **Signal Filtering**: How to filter and analyze specific signals
4. **Zone Analysis**: Detailed analysis of support/resistance zones
5. **Simple Backtesting**: Basic strategy using breakout signals

Run examples:

```bash
python example_usage.py
```

## Visualization Features

The visualizer creates interactive Plotly charts with:

- Candlestick price chart
- Support/resistance zones (shaded areas)
- Support/resistance levels (lines)
- Manipulation zones (liquidity sweeps)
- Trading signals (markers with labels)
- Swing highs/lows (diamonds)
- Volume subplot (optional)

### Customizing Charts

```python
visualizer = SRVisualizer(indicator)
fig = visualizer.plot(
    df_with_signals,
    title="My Analysis",
    show_volume=True,        # Show volume subplot
    show_signals=True,       # Show trading signals
    show_zones=True,         # Show S/R zones
    show_manipulation=True,  # Show manipulation zones
    show_swings=True,        # Show swing highs/lows
    width=1400,              # Chart width
    height=800               # Chart height
)

# Save to HTML
visualizer.save_html(fig, "my_analysis.html")

# Show in browser
visualizer.show(fig)
```

## Accessing Zones

```python
zones = indicator.get_zones()

# Get resistance zones
for zone in zones['resistance']:
    print(f"Level: {zone.level}")
    print(f"Range: {zone.bottom} - {zone.top}")
    print(f"Broken: {zone.b}")
    print(f"Tested: {zone.t}")

# Get support zones
for zone in zones['support']:
    print(f"Level: {zone.level}")
    print(f"Range: {zone.bottom} - {zone.top}")
```

## Tips for Different Market Conditions

### Ranging Markets
- Increase `detection_length` (20-30)
- Increase `sr_margin` (2.5-3.5)
- Enable `check_historical_sr`

### Trending Markets
- Decrease `detection_length` (10-15)
- Decrease `sr_margin` (1.5-2.0)
- Disable `check_historical_sr` for faster adaptation

### Volatile Markets (Crypto)
- Increase `detection_length` (20-30)
- Increase `sr_margin` (3.0-4.0)
- Increase `mn_margin` (2.0-3.0)
- Enable `avoid_false_breakouts`

## License

This work is licensed under a Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
https://creativecommons.org/licenses/by-nc-sa/4.0/

© LuxAlgo (Original Pine Script indicator)

## Credits

Original Pine Script indicator by LuxAlgo
Python translation maintains the core logic and algorithms from the original implementation.

## Differences from Pine Script Version

1. **Multi-timeframe**: The Python version uses single timeframe data. To analyze different timeframes, resample your data before passing to the indicator.
2. **Alerts**: Python version doesn't include real-time alerts. You can implement your own alert system using the signal columns.
3. **Performance**: Python implementation processes historical data efficiently but isn't optimized for tick-by-tick real-time processing.

## Future Enhancements

Potential additions:
- Real-time data streaming support
- Backtesting framework integration (backtrader, etc.)
- Additional visualization backends (matplotlib, mplfinance)
- Multi-timeframe analysis support
- Alert system with notifications
- Strategy templates

## Troubleshooting

**No signals detected:**
- Adjust `detection_length` based on your timeframe
- Ensure you have enough historical data (at least 2x detection_length)
- Try different `sr_margin` values

**Too many signals:**
- Increase `detection_length`
- Increase `sr_margin` for wider zones
- Enable `avoid_false_breakouts`

**Zones not showing:**
- Check if pivots are being detected
- Verify your data has sufficient price movement
- Reduce `sr_margin` for tighter zones

## Contributing

Feel free to submit issues, improvements, or feature requests!
