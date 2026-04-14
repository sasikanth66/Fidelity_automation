"""
Example usage of Support and Resistance Indicator
Demonstrates how to load data, calculate signals, and visualize results
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from support_resistance_indicator import SupportResistanceIndicator
from sr_visualizer import SRVisualizer


def download_sample_data(symbol: str = "AAPL", period: str = "6mo", interval: str = "1d"):
    """
    Download sample OHLCV data from Yahoo Finance

    Parameters
    ----------
    symbol : str
        Ticker symbol (default: AAPL)
    period : str
        Data period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    interval : str
        Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo

    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV data
    """
    print(f"Downloading {symbol} data...")
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    # Rename columns to lowercase
    df.columns = df.columns.str.lower()

    # Keep only OHLCV columns
    df = df[['open', 'high', 'low', 'close', 'volume']]

    print(f"Downloaded {len(df)} bars")
    return df


def load_csv_data(filepath: str):
    """
    Load OHLCV data from CSV file

    Parameters
    ----------
    filepath : str
        Path to CSV file

    Expected CSV format:
    - Columns: date, open, high, low, close, volume
    - OR: timestamp, open, high, low, close, volume

    Returns
    -------
    pd.DataFrame
        DataFrame with OHLCV data
    """
    df = pd.read_csv(filepath)

    # Convert date/timestamp column to datetime index
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)

    # Ensure columns are lowercase
    df.columns = df.columns.str.lower()

    # Keep only OHLCV columns
    required_cols = ['open', 'high', 'low', 'close']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    if 'volume' not in df.columns:
        df['volume'] = 0
        print("Warning: Volume column not found, using 0 for all bars")

    return df[['open', 'high', 'low', 'close', 'volume']]


def example_basic_usage():
    """Basic usage example with default settings"""
    print("\n=== Basic Usage Example ===\n")

    # Download sample data - NVDA with 1H data (6 months for more history), then resample to 4H
    df = download_sample_data(symbol="NVDA", period="6mo", interval="1h")

    # Resample to 4H timeframe
    print("Resampling to 4H timeframe...")
    df_4h = df.resample('4H').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    print(f"Resampled to {len(df_4h)} 4H bars")

    # Create indicator with lookback period of 20
    indicator = SupportResistanceIndicator(
        detection_length=20,        # Increased from 15 to 20 for better pivot detection
        sr_margin=2.0,
        mn_margin=1.3,
        avoid_false_breakouts=True,
        check_historical_sr=True,   # Important: Check previous S&R levels
        show_manipulation=True
    )

    # Calculate signals
    print("\nCalculating support/resistance zones and signals...")
    df_with_signals = indicator.calculate(df_4h)

    # Print signal summary
    print("\n--- Signal Summary ---")
    print(f"Bullish Breakouts: {df_with_signals['breakout_bullish'].sum()}")
    print(f"Bearish Breakouts: {df_with_signals['breakout_bearish'].sum()}")
    print(f"Bullish Tests: {df_with_signals['test_bullish'].sum()}")
    print(f"Bearish Tests: {df_with_signals['test_bearish'].sum()}")
    print(f"Bullish Retests: {df_with_signals['retest_bullish'].sum()}")
    print(f"Bearish Retests: {df_with_signals['retest_bearish'].sum()}")
    print(f"Bullish Rejections: {df_with_signals['rejection_bullish'].sum()}")
    print(f"Bearish Rejections: {df_with_signals['rejection_bearish'].sum()}")

    # Get zones
    zones = indicator.get_zones()
    print(f"\nActive Resistance Zones: {len(zones['resistance'])}")
    print(f"Active Support Zones: {len(zones['support'])}")

    # Create visualization
    print("\nCreating visualization...")
    visualizer = SRVisualizer(indicator)
    fig = visualizer.plot(
        df_with_signals,
        title="NVDA - Support and Resistance Analysis (4H Timeframe, 6 Month History)",
        show_volume=True,
        show_signals=True,
        show_zones=True,
        show_manipulation=True,
        show_swings=True
    )

    # Save to HTML
    visualizer.save_html(fig, "nvda_4h_sr_analysis.html")

    # Show interactive chart
    visualizer.show(fig)

    return df_with_signals, indicator


def example_custom_settings():
    """Example with custom settings for different market conditions"""
    print("\n=== Custom Settings Example ===\n")

    # Download crypto data (more volatile)
    df = download_sample_data(symbol="BTC-USD", period="3mo", interval="1h")

    # Create indicator with custom settings for volatile markets
    indicator = SupportResistanceIndicator(
        detection_length=20,      # Longer detection for stability
        sr_margin=3.0,            # Wider zones for volatility
        mn_margin=2.0,            # Larger manipulation threshold
        avoid_false_breakouts=True,
        check_historical_sr=False,  # Only check most recent zones
        show_manipulation=True
    )

    # Calculate signals
    print("Calculating support/resistance zones and signals...")
    df_with_signals = indicator.calculate(df)

    # Create visualization
    visualizer = SRVisualizer(indicator)
    fig = visualizer.plot(
        df_with_signals,
        title="BTC-USD - Support and Resistance Analysis (Custom Settings)",
        show_volume=True,
        show_signals=True,
        show_zones=True,
        show_manipulation=True,
        show_swings=False  # Hide swings for cleaner chart
    )

    visualizer.save_html(fig, "btc_sr_analysis.html")
    visualizer.show(fig)

    return df_with_signals, indicator


def example_signal_filtering():
    """Example showing how to filter and use specific signals"""
    print("\n=== Signal Filtering Example ===\n")

    # Download data
    df = download_sample_data(symbol="SPY", period="1y", interval="1d")

    # Calculate signals
    indicator = SupportResistanceIndicator()
    df_with_signals = indicator.calculate(df)

    # Filter for bullish signals only
    bullish_signals = df_with_signals[
        (df_with_signals['breakout_bullish']) |
        (df_with_signals['test_bullish']) |
        (df_with_signals['retest_bullish']) |
        (df_with_signals['rejection_bullish'])
    ]

    print(f"\nTotal Bullish Signals: {len(bullish_signals)}")
    print("\nRecent Bullish Signals:")
    print(bullish_signals.tail(10)[['close', 'breakout_bullish', 'test_bullish',
                                     'retest_bullish', 'rejection_bullish']])

    # Filter for bearish signals only
    bearish_signals = df_with_signals[
        (df_with_signals['breakout_bearish']) |
        (df_with_signals['test_bearish']) |
        (df_with_signals['retest_bearish']) |
        (df_with_signals['rejection_bearish'])
    ]

    print(f"\nTotal Bearish Signals: {len(bearish_signals)}")

    # Get only breakout signals
    breakouts = df_with_signals[
        (df_with_signals['breakout_bullish']) |
        (df_with_signals['breakout_bearish'])
    ]

    print(f"\nTotal Breakouts: {len(breakouts)}")
    print("\nRecent Breakouts:")
    print(breakouts.tail(5)[['close', 'breakout_bullish', 'breakout_bearish']])

    return df_with_signals


def example_zone_analysis():
    """Example showing how to analyze support/resistance zones"""
    print("\n=== Zone Analysis Example ===\n")

    # Download data
    df = download_sample_data(symbol="TSLA", period="6mo", interval="1d")

    # Calculate
    indicator = SupportResistanceIndicator()
    df_with_signals = indicator.calculate(df)

    # Get zones
    zones = indicator.get_zones()

    print("=== Resistance Zones ===")
    for i, zone in enumerate(zones['resistance'][:5]):  # Top 5 resistance zones
        print(f"\nResistance Zone {i+1}:")
        print(f"  Level: ${zone.level:.2f}")
        print(f"  Range: ${zone.bottom:.2f} - ${zone.top:.2f}")
        print(f"  Duration: {zone.right - zone.left} bars")
        print(f"  Broken: {zone.b}")
        print(f"  Tested: {zone.t}")
        print(f"  Retested: {zone.r}")
        if zone.lq_top is not None:
            print(f"  Manipulation Zone: ${zone.lq_bottom:.2f} - ${zone.lq_top:.2f}")

    print("\n=== Support Zones ===")
    for i, zone in enumerate(zones['support'][:5]):  # Top 5 support zones
        print(f"\nSupport Zone {i+1}:")
        print(f"  Level: ${zone.level:.2f}")
        print(f"  Range: ${zone.bottom:.2f} - ${zone.top:.2f}")
        print(f"  Duration: {zone.right - zone.left} bars")
        print(f"  Broken: {zone.b}")
        print(f"  Tested: {zone.t}")
        print(f"  Retested: {zone.r}")
        if zone.lq_bottom is not None:
            print(f"  Manipulation Zone: ${zone.lq_bottom:.2f} - ${zone.lq_top:.2f}")

    return zones


def example_backtesting_simple():
    """Simple backtesting example using signals"""
    print("\n=== Simple Backtesting Example ===\n")

    # Download data
    df = download_sample_data(symbol="AAPL", period="1y", interval="1d")

    # Calculate signals
    indicator = SupportResistanceIndicator()
    df_with_signals = indicator.calculate(df)

    # Simple strategy: Buy on bullish breakout, sell on bearish breakout
    position = 0
    trades = []
    entry_price = 0

    for i in range(len(df_with_signals)):
        if df_with_signals['breakout_bullish'].iloc[i] and position == 0:
            # Buy signal
            entry_price = df_with_signals['close'].iloc[i]
            position = 1
            trades.append({
                'date': df_with_signals.index[i],
                'type': 'BUY',
                'price': entry_price
            })

        elif df_with_signals['breakout_bearish'].iloc[i] and position == 1:
            # Sell signal
            exit_price = df_with_signals['close'].iloc[i]
            profit = (exit_price - entry_price) / entry_price * 100
            position = 0
            trades.append({
                'date': df_with_signals.index[i],
                'type': 'SELL',
                'price': exit_price,
                'profit_pct': profit
            })

    # Print results
    print(f"Total Trades: {len([t for t in trades if t['type'] == 'SELL'])}")

    sell_trades = [t for t in trades if t['type'] == 'SELL']
    if sell_trades:
        avg_profit = sum(t['profit_pct'] for t in sell_trades) / len(sell_trades)
        print(f"Average Profit per Trade: {avg_profit:.2f}%")

        print("\nTrade History:")
        for trade in trades[:10]:  # Show first 10 trades
            if trade['type'] == 'BUY':
                print(f"{trade['date'].date()} - BUY at ${trade['price']:.2f}")
            else:
                print(f"{trade['date'].date()} - SELL at ${trade['price']:.2f} (Profit: {trade['profit_pct']:.2f}%)")

    return trades


if __name__ == "__main__":
    """
    Run examples

    Uncomment the example you want to run, or run all of them
    """

    # Example 1: Basic usage
    df, indicator = example_basic_usage()

    # Example 2: Custom settings for volatile markets
    # df, indicator = example_custom_settings()

    # Example 3: Filter and analyze signals
    # df = example_signal_filtering()

    # Example 4: Analyze zones in detail
    # zones = example_zone_analysis()

    # Example 5: Simple backtesting
    # trades = example_backtesting_simple()

    print("\n=== Examples Complete ===")
    print("\nCheck the generated HTML files for interactive charts:")
    print("  - nvda_4h_sr_analysis.html")
    print("  - btc_sr_analysis.html (if example_custom_settings was run)")
