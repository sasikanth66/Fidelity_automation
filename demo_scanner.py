"""
Stock Scanner Demo with Sample Data
Demonstrates scanner functionality when Yahoo Finance is blocked
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from support_resistance_indicator import SupportResistanceIndicator
from typing import List, Dict
import random


def generate_sample_stock_data(
    symbol: str,
    bars: int = 720,
    base_price: float = 100,
    volatility: float = 0.02,
    trend: float = 0.0001,
    create_bounce: str = None  # 'support', 'resistance', or None
) -> pd.DataFrame:
    """
    Generate realistic sample stock data with optional bounce pattern

    Parameters
    ----------
    symbol : str
        Stock symbol
    bars : int
        Number of 4H bars to generate
    base_price : float
        Starting price
    volatility : float
        Price volatility
    trend : float
        Trend direction (positive = uptrend)
    create_bounce : str
        'support' to create support bounce, 'resistance' for resistance bounce
    """
    dates = pd.date_range(end=datetime.now(), periods=bars, freq='4H')

    # Generate price series with trend
    np.random.seed(hash(symbol) % 2**32)  # Reproducible but different per symbol

    prices = [base_price]
    for i in range(1, bars):
        change = np.random.randn() * volatility + trend
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)

    prices = np.array(prices)

    # Create OHLC
    df = pd.DataFrame(index=dates)
    df['close'] = prices

    # Add realistic OHLC
    df['open'] = df['close'].shift(1).fillna(df['close'].iloc[0])
    df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.randn(len(df)) * 0.005))
    df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.randn(len(df)) * 0.005))
    df['volume'] = np.random.randint(1000000, 10000000, len(df))

    # Create bounce pattern if requested
    if create_bounce == 'support':
        # Create a support level around current price - 5%
        support_level = df['close'].iloc[-20] * 0.95

        # Make price touch support in last 3 bars and bounce
        bounce_bar = len(df) - random.randint(1, 3)
        df.loc[df.index[bounce_bar], 'low'] = support_level * 0.995
        df.loc[df.index[bounce_bar], 'close'] = support_level * 1.01

        # Bullish follow-through
        for i in range(bounce_bar + 1, len(df)):
            df.loc[df.index[i], 'close'] = df['close'].iloc[bounce_bar] * (1 + (i - bounce_bar) * 0.005)
            df.loc[df.index[i], 'open'] = df['close'].iloc[i-1]
            df.loc[df.index[i], 'high'] = df['close'].iloc[i] * 1.005
            df.loc[df.index[i], 'low'] = df['open'].iloc[i] * 0.995

    elif create_bounce == 'resistance':
        # Create a resistance level around current price + 5%
        resistance_level = df['close'].iloc[-20] * 1.05

        # Make price touch resistance in last 3 bars and bounce down
        bounce_bar = len(df) - random.randint(1, 3)
        df.loc[df.index[bounce_bar], 'high'] = resistance_level * 1.005
        df.loc[df.index[bounce_bar], 'close'] = resistance_level * 0.99

        # Bearish follow-through
        for i in range(bounce_bar + 1, len(df)):
            df.loc[df.index[i], 'close'] = df['close'].iloc[bounce_bar] * (1 - (i - bounce_bar) * 0.005)
            df.loc[df.index[i], 'open'] = df['close'].iloc[i-1]
            df.loc[df.index[i], 'high'] = df['open'].iloc[i] * 1.005
            df.loc[df.index[i], 'low'] = df['close'].iloc[i] * 0.995

    return df


class DemoScanner:
    """Demo scanner using sample data"""

    def __init__(self):
        self.results = {
            'support_bounces': [],
            'resistance_bounces': []
        }

        # Create demo stocks with different patterns
        self.demo_stocks = {
            'NVDA': {'base': 485, 'bounce': 'support'},
            'AMD': {'base': 142, 'bounce': 'support'},
            'AAPL': {'base': 178, 'bounce': None},
            'MSFT': {'base': 378, 'bounce': None},
            'TSLA': {'base': 245, 'bounce': 'resistance'},
            'GOOGL': {'base': 142, 'bounce': None},
            'META': {'base': 485, 'bounce': 'support'},
            'AMZN': {'base': 175, 'bounce': None},
            'NFLX': {'base': 485, 'bounce': None},
            'AVGO': {'base': 1250, 'bounce': 'resistance'},
        }

    def scan_all(self):
        """Scan all demo stocks"""
        print("\n" + "="*80)
        print("DEMO SCANNER - Sample Data")
        print("="*80)
        print("\nScanning 10 demo stocks with realistic patterns...\n")
        print("="*80 + "\n")

        for i, (symbol, config) in enumerate(self.demo_stocks.items(), 1):
            print(f"[{i}/10] Scanning {symbol}...", end=" ")
            self.scan_stock(symbol, config)

        print("\n" + "="*80)
        print("DEMO SCAN COMPLETE")
        print("="*80 + "\n")

    def scan_stock(self, symbol: str, config: Dict):
        """Scan a single demo stock"""
        # Generate data
        df = generate_sample_stock_data(
            symbol=symbol,
            bars=720,
            base_price=config['base'],
            volatility=0.015,
            trend=0.0001,
            create_bounce=config['bounce']
        )

        # Calculate S&R
        indicator = SupportResistanceIndicator(
            detection_length=20,
            sr_margin=2.0,
            mn_margin=1.3,
            avoid_false_breakouts=True,
            check_historical_sr=True,
            show_manipulation=True
        )

        df_signals = indicator.calculate(df)
        zones = indicator.get_zones()

        # Check for bounces
        support_bounce, support_info = self.check_support_bounce(df_signals, zones['support'])
        resistance_bounce, resistance_info = self.check_resistance_bounce(df_signals, zones['resistance'])

        result = {
            'symbol': symbol,
            'current_price': df['close'].iloc[-1],
            'support_bounce': support_bounce,
            'resistance_bounce': resistance_bounce,
            'support_info': support_info if support_bounce else None,
            'resistance_info': resistance_info if resistance_bounce else None,
        }

        if support_bounce:
            print(f"✅ SUPPORT BOUNCE (${support_info['zone_level']:.2f})")
            self.results['support_bounces'].append(result)
        elif resistance_bounce:
            print(f"✅ RESISTANCE BOUNCE (${resistance_info['zone_level']:.2f})")
            self.results['resistance_bounces'].append(result)
        else:
            print("⚪ No bounce")

    def check_support_bounce(self, df, zones):
        """Check for support bounce"""
        if len(zones) == 0 or len(df) < 3:
            return False, {}

        for zone in zones[:2]:
            recent_bars = df.tail(3)

            for i in range(len(recent_bars)):
                bar = recent_bars.iloc[i]
                touched_support = bar['low'] <= zone.top and bar['low'] >= zone.bottom * 0.99

                if touched_support:
                    bounced = bar['close'] > zone.bottom

                    if bounced and i < len(recent_bars) - 1:
                        next_bars = recent_bars.iloc[i+1:]
                        bullish_follow_through = (next_bars['close'] > zone.bottom).any()

                        if bullish_follow_through:
                            return True, {
                                'zone_level': zone.level,
                                'zone_bottom': zone.bottom,
                                'zone_top': zone.top,
                                'touch_price': bar['low'],
                                'bounce_close': bar['close'],
                                'bars_ago': len(recent_bars) - i - 1,
                                'current_price': df['close'].iloc[-1],
                                'distance_pct': ((df['close'].iloc[-1] - zone.level) / zone.level) * 100
                            }

        return False, {}

    def check_resistance_bounce(self, df, zones):
        """Check for resistance bounce"""
        if len(zones) == 0 or len(df) < 3:
            return False, {}

        for zone in zones[:2]:
            recent_bars = df.tail(3)

            for i in range(len(recent_bars)):
                bar = recent_bars.iloc[i]
                touched_resistance = bar['high'] >= zone.bottom and bar['high'] <= zone.top * 1.01

                if touched_resistance:
                    bounced = bar['close'] < zone.top

                    if bounced and i < len(recent_bars) - 1:
                        next_bars = recent_bars.iloc[i+1:]
                        bearish_follow_through = (next_bars['close'] < zone.top).any()

                        if bearish_follow_through:
                            return True, {
                                'zone_level': zone.level,
                                'zone_bottom': zone.bottom,
                                'zone_top': zone.top,
                                'touch_price': bar['high'],
                                'bounce_close': bar['close'],
                                'bars_ago': len(recent_bars) - i - 1,
                                'current_price': df['close'].iloc[-1],
                                'distance_pct': ((zone.level - df['close'].iloc[-1]) / zone.level) * 100
                            }

        return False, {}

    def print_results(self):
        """Print demo results"""
        print("\n" + "="*100)
        print("🟢 STOCKS BOUNCING OFF SUPPORT (BULLISH SETUPS)")
        print("="*100)

        if not self.results['support_bounces']:
            print("No support bounces found.")
        else:
            print(f"\nFound {len(self.results['support_bounces'])} stocks:\n")
            print(f"{'Symbol':<8} {'Price':<10} {'Support':<10} {'Distance':<12} {'Bars Ago':<10} {'Strength'}")
            print("-" * 100)

            for result in sorted(self.results['support_bounces'],
                                key=lambda x: abs(x['support_info']['distance_pct'])):
                info = result['support_info']
                strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"

                print(f"{result['symbol']:<8} "
                      f"${result['current_price']:<9.2f} "
                      f"${info['zone_level']:<9.2f} "
                      f"+{info['distance_pct']:<11.2f}% "
                      f"{info['bars_ago']:<10} "
                      f"{strength}")

        print("\n" + "="*100)
        print("🔴 STOCKS BOUNCING OFF RESISTANCE (BEARISH SETUPS)")
        print("="*100)

        if not self.results['resistance_bounces']:
            print("No resistance bounces found.")
        else:
            print(f"\nFound {len(self.results['resistance_bounces'])} stocks:\n")
            print(f"{'Symbol':<8} {'Price':<10} {'Resistance':<12} {'Distance':<12} {'Bars Ago':<10} {'Strength'}")
            print("-" * 100)

            for result in sorted(self.results['resistance_bounces'],
                                key=lambda x: abs(x['resistance_info']['distance_pct'])):
                info = result['resistance_info']
                strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"

                print(f"{result['symbol']:<8} "
                      f"${result['current_price']:<9.2f} "
                      f"${info['zone_level']:<11.2f} "
                      f"-{info['distance_pct']:<11.2f}% "
                      f"{info['bars_ago']:<10} "
                      f"{strength}")

        print("\n" + "="*100)
        print("\n💡 This is DEMO DATA showing how the scanner works.")
        print("   When you have network access, use stock_scanner.py for real data.")
        print("\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("STOCK SCANNER DEMO")
    print("="*80)
    print("\nThis demo uses sample data to show how the scanner works.")
    print("It creates realistic price patterns with actual support/resistance bounces.")
    print("\n" + "="*80)

    scanner = DemoScanner()
    scanner.scan_all()
    scanner.print_results()

    print("\n✅ Demo complete!")
    print("\nNext steps:")
    print("  1. When you have network access, run: python stock_scanner.py")
    print("  2. Or provide CSV files with historical data")
    print("  3. The scanner works the same way with real data")
