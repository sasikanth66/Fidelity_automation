"""
Quick Visualizer for Scanner Results
Easily visualize stocks identified by the scanner
"""

import yfinance as yf
import pandas as pd
from support_resistance_indicator import SupportResistanceIndicator
from sr_visualizer import SRVisualizer
import sys


def visualize_stock(
    symbol: str,
    period: str = "6mo",
    interval: str = "1h",
    timeframe: str = "4H",
    detection_length: int = 20
):
    """
    Visualize a stock with S&R zones

    Parameters
    ----------
    symbol : str
        Stock symbol (e.g., 'NVDA')
    period : str
        Data period (default: '6mo')
    interval : str
        Download interval (default: '1h')
    timeframe : str
        Resampling timeframe (default: '4H')
    detection_length : int
        Lookback for pivots (default: 20)
    """
    print(f"\n📊 Analyzing {symbol}...\n")

    # Download data
    print("Downloading data...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    if df.empty:
        print(f"❌ No data available for {symbol}")
        return

    # Prepare data
    df.columns = df.columns.str.lower()
    df = df[['open', 'high', 'low', 'close', 'volume']]

    # Resample
    print(f"Resampling to {timeframe}...")
    df_resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    print(f"Bars: {len(df_resampled)}")

    # Calculate S&R
    print("Calculating support/resistance zones...")
    indicator = SupportResistanceIndicator(
        detection_length=detection_length,
        sr_margin=2.0,
        mn_margin=1.3,
        avoid_false_breakouts=True,
        check_historical_sr=True,
        show_manipulation=True
    )

    df_signals = indicator.calculate(df_resampled)

    # Get zones
    zones = indicator.get_zones()
    print(f"\nZones found:")
    print(f"  - Support zones: {len(zones['support'])}")
    print(f"  - Resistance zones: {len(zones['resistance'])}")

    # Show recent price action
    current_price = df_signals['close'].iloc[-1]
    print(f"\nCurrent price: ${current_price:.2f}")

    # Show nearest zones
    if zones['support']:
        nearest_support = min(zones['support'], key=lambda z: abs(z.level - current_price))
        distance = ((current_price - nearest_support.level) / nearest_support.level) * 100
        print(f"Nearest support: ${nearest_support.level:.2f} ({distance:+.2f}%)")

    if zones['resistance']:
        nearest_resistance = min(zones['resistance'], key=lambda z: abs(z.level - current_price))
        distance = ((nearest_resistance.level - current_price) / current_price) * 100
        print(f"Nearest resistance: ${nearest_resistance.level:.2f} ({distance:+.2f}%)")

    # Visualize
    print("\nGenerating chart...")
    visualizer = SRVisualizer(indicator)
    fig = visualizer.plot(
        df_signals,
        title=f"{symbol} - Support & Resistance Analysis ({timeframe})",
        show_volume=True,
        show_signals=True,
        show_zones=True,
        show_manipulation=True,
        show_swings=True
    )

    # Save and show
    filename = f"{symbol.lower()}_analysis.html"
    visualizer.save_html(fig, filename)
    print(f"✅ Chart saved to {filename}")

    visualizer.show(fig)


def quick_viz(symbols: list, **kwargs):
    """
    Quickly visualize multiple stocks

    Parameters
    ----------
    symbols : list
        List of stock symbols
    **kwargs : dict
        Additional parameters for visualize_stock()
    """
    for symbol in symbols:
        visualize_stock(symbol, **kwargs)
        print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    """
    Usage examples:

    # Visualize single stock
    python visualize_scanner_results.py NVDA

    # Or run from Python
    from visualize_scanner_results import visualize_stock
    visualize_stock('NVDA')

    # Visualize multiple stocks
    from visualize_scanner_results import quick_viz
    quick_viz(['NVDA', 'AMD', 'AAPL'])
    """

    if len(sys.argv) > 1:
        # Command line usage
        symbol = sys.argv[1].upper()
        visualize_stock(symbol)
    else:
        # Default: visualize NVDA
        print("Usage: python visualize_scanner_results.py SYMBOL")
        print("\nExample with NVDA:")
        visualize_stock('NVDA')
