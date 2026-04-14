"""
Fetch technical data for a single stock symbol.
Usage: python fetch_technical_data.py <SYMBOL>
Outputs JSON to stdout with RSI, S/R levels, volume ratio, price change.
"""

import json
import sys

import pandas as pd
import numpy as np
import yfinance as yf

from support_resistance_indicator import SupportResistanceIndicator


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI using EWM (matches TradingView)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def download_and_resample(symbol: str) -> pd.DataFrame:
    """Download 6mo 1H data and resample to 4H bars."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(period='6mo', interval='1h')

    if df.empty:
        raise ValueError(f"No data returned for {symbol}")

    df.columns = df.columns.str.lower()
    df = df[['open', 'high', 'low', 'close', 'volume']]

    df_4h = df.resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }).dropna()

    return df_4h


def get_nearest_levels(zones: dict, current_price: float):
    """Find nearest support below price and nearest resistance above price."""
    nearest_support = None
    nearest_resistance = None

    for zone in zones.get('support', []):
        level = zone.level
        if level < current_price:
            if nearest_support is None or level > nearest_support:
                nearest_support = level

    for zone in zones.get('resistance', []):
        level = zone.level
        if level > current_price:
            if nearest_resistance is None or level < nearest_resistance:
                nearest_resistance = level

    return nearest_support, nearest_resistance


def analyze(symbol: str) -> dict:
    df_4h = download_and_resample(symbol)

    if len(df_4h) < 30:
        raise ValueError(f"Insufficient data for {symbol}: {len(df_4h)} bars")

    # RSI on 4H close
    rsi_series = compute_rsi(df_4h['close'], period=14)
    rsi = float(rsi_series.iloc[-1]) if not np.isnan(rsi_series.iloc[-1]) else None

    # S/R zones
    indicator = SupportResistanceIndicator(detection_length=20, sr_margin=2.0, mn_margin=1.3)
    indicator.calculate(df_4h)
    zones = indicator.get_zones()

    current_price = float(df_4h['close'].iloc[-1])
    nearest_support, nearest_resistance = get_nearest_levels(zones, current_price)

    support_distance_pct = (
        round((current_price - nearest_support) / current_price * 100, 2)
        if nearest_support is not None else None
    )
    resistance_distance_pct = (
        round((nearest_resistance - current_price) / current_price * 100, 2)
        if nearest_resistance is not None else None
    )

    # Volume ratio: 5-bar avg / 50-bar avg
    vol = df_4h['volume']
    recent_volume_ratio = None
    if len(vol) >= 50:
        avg5 = float(vol.iloc[-5:].mean())
        avg50 = float(vol.iloc[-50:].mean())
        recent_volume_ratio = round(avg5 / avg50, 3) if avg50 > 0 else None

    # Price change over last 5 bars
    recent_price_change_pct = None
    if len(df_4h) >= 6:
        price_5_bars_ago = float(df_4h['close'].iloc[-6])
        recent_price_change_pct = round(
            (current_price - price_5_bars_ago) / price_5_bars_ago * 100, 2
        )

    return {
        'symbol': symbol,
        'current_price': round(current_price, 4),
        'rsi': round(rsi, 2) if rsi is not None else None,
        'nearest_support': round(nearest_support, 4) if nearest_support is not None else None,
        'nearest_resistance': round(nearest_resistance, 4) if nearest_resistance is not None else None,
        'support_distance_pct': support_distance_pct,
        'resistance_distance_pct': resistance_distance_pct,
        'recent_volume_ratio': recent_volume_ratio,
        'recent_price_change_pct': recent_price_change_pct,
        'error': None,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python fetch_technical_data.py <SYMBOL>'}))
        sys.exit(1)

    symbol = sys.argv[1].upper().strip()

    try:
        result = analyze(symbol)
        print(
            f"{symbol}: price=${result['current_price']}  RSI={result['rsi']}  "
            f"vol={result['recent_volume_ratio']}x  chg={result['recent_price_change_pct']}%  "
            f"sup={result['nearest_support']}  res={result['nearest_resistance']}",
            file=sys.stderr,
        )
    except Exception as e:
        result = {
            'symbol': symbol,
            'current_price': None,
            'rsi': None,
            'nearest_support': None,
            'nearest_resistance': None,
            'support_distance_pct': None,
            'resistance_distance_pct': None,
            'recent_volume_ratio': None,
            'recent_price_change_pct': None,
            'error': str(e),
        }
        print(f"{symbol}: ERROR - {e}", file=sys.stderr)

    print(json.dumps(result))


if __name__ == '__main__':
    main()
