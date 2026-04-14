"""
Stock Scanner for Support/Resistance Breakouts
Scans stocks to find ones that recently broke through S&R levels
"""

import pandas as pd
import yfinance as yf
from datetime import datetime
import time
from typing import List, Dict, Tuple
from support_resistance_indicator import SupportResistanceIndicator
import warnings
warnings.filterwarnings('ignore')


# NASDAQ-100 stocks (major components)
NASDAQ_100 = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ASML', 'COST',
    'NFLX', 'AMD', 'PEP', 'ADBE', 'CSCO', 'TMUS', 'CMCSA', 'INTC', 'TXN', 'QCOM',
    'AMGN', 'INTU', 'HON', 'AMAT', 'SBUX', 'ISRG', 'BKNG', 'VRTX', 'ADP', 'GILD',
    'ADI', 'REGN', 'MU', 'LRCX', 'PANW', 'MDLZ', 'PYPL', 'KLAC', 'SNPS', 'CDNS',
    'MELI', 'CRWD', 'MAR', 'MRVL', 'CSX', 'ORLY', 'ADSK', 'FTNT', 'DASH', 'ABNB',
    'NXPI', 'WDAY', 'CPRT', 'CHTR', 'MNST', 'AEP', 'PAYX', 'ROST', 'ODFL', 'FAST',
    'BKR', 'KDP', 'EA', 'VRSK', 'CTSH', 'GEHC', 'DXCM', 'EXC', 'CTAS', 'IDXX',
    'LULU', 'KHC', 'PCAR', 'ZS', 'BIIB', 'CCEP', 'TTWO', 'TEAM', 'ILMN', 'ANSS',
    'XEL', 'FANG', 'WBD', 'CSGP', 'ON', 'DLTR', 'CDW', 'DDOG', 'MDB', 'GFS',
    'WBA', 'MRNA', 'EBAY', 'ZM', 'ENPH', 'SMCI', 'ALGN', 'RIVN', 'LCID', 'ARM'
]


class BreakoutScanner:
    """
    Scanner to identify stocks breaking through support or resistance levels

    Parameters
    ----------
    stocks : List[str]
        List of stock symbols to scan
    period : str
        Data period (default: "6mo")
    interval : str
        Data interval (default: "1h")
    timeframe : str
        Resampling timeframe (default: "4H")
    detection_length : int
        Lookback period for pivot detection (default: 20)
    lookback_bars : int
        Number of recent bars to check for breakouts (default: 3)
    min_breakout_pct : float
        Minimum percentage move through zone to confirm breakout (default: 0.5%)
    """

    def __init__(
        self,
        stocks: List[str] = None,
        period: str = "6mo",
        interval: str = "1h",
        timeframe: str = "4H",
        detection_length: int = 20,
        lookback_bars: int = 3,
        min_breakout_pct: float = 0.5
    ):
        self.stocks = stocks or NASDAQ_100
        self.period = period
        self.interval = interval
        self.timeframe = timeframe
        self.detection_length = detection_length
        self.lookback_bars = lookback_bars
        self.min_breakout_pct = min_breakout_pct

        self.results = {
            'bullish_breakouts': [],
            'bearish_breakouts': []
        }

    def download_and_resample(self, symbol: str) -> pd.DataFrame:
        """Download and resample stock data"""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=self.period, interval=self.interval)

            if df.empty:
                return None

            # Rename columns to lowercase
            df.columns = df.columns.str.lower()
            df = df[['open', 'high', 'low', 'close', 'volume']]

            # Resample to target timeframe
            df_resampled = df.resample(self.timeframe).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()

            return df_resampled

        except Exception as e:
            print(f"  Error downloading {symbol}: {str(e)}")
            return None

    def check_bullish_breakout(self, df: pd.DataFrame, zones: List) -> Tuple[bool, Dict]:
        """
        Check if stock recently broke above resistance (bullish breakout)

        A bullish breakout occurs when:
        1. Price breaks above a resistance zone within the lookback period
        2. Close is above the resistance zone (strong close)
        3. Price is CURRENTLY staying above the resistance level
        4. Price was BELOW the resistance before breaking above

        Returns
        -------
        Tuple[bool, Dict]
            (breakout_detected, breakout_info)
        """
        if len(zones) == 0 or len(df) < self.lookback_bars + 1:
            return False, {}
        
        # Current price must be above the resistance to confirm breakout is holding
        current_price = df['close'].iloc[-1]

        # Check most recent resistance zones
        for zone in zones[:3]:  # Check latest 3 resistance zones
            # Filter out zones that are too far from current price (>20% away)
            # This prevents detecting breakouts from ancient price levels
            distance_from_current = abs(current_price - zone.level) / current_price
            if distance_from_current > 0.20:  # Zone is more than 20% away
                continue
            
            # First check: Is current price staying above the resistance?
            if current_price <= zone.top:
                continue  # Skip this zone if we're not currently above it
            
            # Look at last N bars to find the breakout
            # Also get one bar before to check if price was below resistance
            recent_bars = df.tail(self.lookback_bars + 1)

            for i in range(1, len(recent_bars)):  # Start from index 1 to have a previous bar
                bar = recent_bars.iloc[i]
                prev_bar = recent_bars.iloc[i-1]

                # Check if price broke above resistance in this bar
                # AND was below resistance in the previous bar
                broke_resistance = bar['high'] > zone.top
                was_below_resistance = prev_bar['close'] <= zone.top

                if broke_resistance and was_below_resistance:
                    # Confirm with strong close above resistance
                    strong_close = bar['close'] > zone.top
                    
                    # Calculate breakout strength (how far above resistance)
                    breakout_pct = ((bar['close'] - zone.level) / zone.level) * 100

                    if strong_close and breakout_pct >= self.min_breakout_pct:
                        # Verify that price stayed above resistance after the breakout
                        # Check all bars from breakout to current
                        if i < len(recent_bars) - 1:
                            next_bars = recent_bars.iloc[i+1:]
                            # All subsequent bars should close above the resistance top
                            stayed_above = (next_bars['close'] > zone.top).all()
                        else:
                            stayed_above = True  # Current bar is the breakout
                        
                        if stayed_above:
                            return True, {
                                'zone_level': zone.level,
                                'zone_bottom': zone.bottom,
                                'zone_top': zone.top,
                                'breakout_high': bar['high'],
                                'breakout_close': bar['close'],
                                'bars_ago': len(recent_bars) - i - 1,
                                'current_price': current_price,
                                'breakout_pct': breakout_pct,
                                'distance_pct': ((current_price - zone.level) / zone.level) * 100
                            }

        return False, {}

    def check_bearish_breakout(self, df: pd.DataFrame, zones: List) -> Tuple[bool, Dict]:
        """
        Check if stock recently broke below support (bearish breakout)

        A bearish breakout occurs when:
        1. Price breaks below a support zone within the lookback period
        2. Close is below the support zone (strong close)
        3. Price is CURRENTLY staying below the support level
        4. Price was ABOVE the support before breaking below

        Returns
        -------
        Tuple[bool, Dict]
            (breakout_detected, breakout_info)
        """
        if len(zones) == 0 or len(df) < self.lookback_bars + 1:
            return False, {}
        
        # Current price must be below the support to confirm breakout is holding
        current_price = df['close'].iloc[-1]

        # Check most recent support zones
        for zone in zones[:3]:  # Check latest 3 support zones
            # Filter out zones that are too far from current price (>20% away)
            # This prevents detecting breakouts from ancient price levels
            distance_from_current = abs(current_price - zone.level) / current_price
            if distance_from_current > 0.20:  # Zone is more than 20% away
                continue
            
            # First check: Is current price staying below the support?
            if current_price >= zone.bottom:
                continue  # Skip this zone if we're not currently below it
            
            # Look at last N bars to find the breakout
            # Also get one bar before to check if price was above support
            recent_bars = df.tail(self.lookback_bars + 1)

            for i in range(1, len(recent_bars)):  # Start from index 1 to have a previous bar
                bar = recent_bars.iloc[i]
                prev_bar = recent_bars.iloc[i-1]

                # Check if price broke below support in this bar
                # AND was above support in the previous bar
                broke_support = bar['low'] < zone.bottom
                was_above_support = prev_bar['close'] >= zone.bottom

                if broke_support and was_above_support:
                    # Confirm with strong close below support
                    strong_close = bar['close'] < zone.bottom
                    
                    # Calculate breakout strength (how far below support)
                    breakout_pct = ((zone.level - bar['close']) / zone.level) * 100

                    if strong_close and breakout_pct >= self.min_breakout_pct:
                        # Verify that price stayed below support after the breakout
                        # Check all bars from breakout to current
                        if i < len(recent_bars) - 1:
                            next_bars = recent_bars.iloc[i+1:]
                            # All subsequent bars should close below the support bottom
                            stayed_below = (next_bars['close'] < zone.bottom).all()
                        else:
                            stayed_below = True  # Current bar is the breakout
                        
                        if stayed_below:
                            return True, {
                                'zone_level': zone.level,
                                'zone_bottom': zone.bottom,
                                'zone_top': zone.top,
                                'breakout_low': bar['low'],
                                'breakout_close': bar['close'],
                                'bars_ago': len(recent_bars) - i - 1,
                                'current_price': current_price,
                                'breakout_pct': breakout_pct,
                                'distance_pct': ((zone.level - current_price) / zone.level) * 100
                            }

        return False, {}

    def scan_stock(self, symbol: str) -> Dict:
        """Scan a single stock for breakouts"""
        print(f"Scanning {symbol}...", end=" ")

        # Download data
        df = self.download_and_resample(symbol)
        if df is None or len(df) < self.detection_length * 2:
            print("❌ Insufficient data")
            return None

        # Calculate S&R zones
        indicator = SupportResistanceIndicator(
            detection_length=self.detection_length,
            sr_margin=2.0,
            mn_margin=1.3,
            avoid_false_breakouts=True,
            check_historical_sr=True,
            show_manipulation=True
        )

        df_signals = indicator.calculate(df)
        
        # Get zones with stale zone filtering (zones not touched in last 50 bars are filtered out)
        current_index = len(df) - 1
        zones = indicator.get_zones(current_index=current_index, max_bars_inactive=50)

        # Check for breakouts
        bullish_breakout, bullish_info = self.check_bullish_breakout(df_signals, zones['resistance'])
        bearish_breakout, bearish_info = self.check_bearish_breakout(df_signals, zones['support'])

        result = {
            'symbol': symbol,
            'current_price': df['close'].iloc[-1],
            'bullish_breakout': bullish_breakout,
            'bearish_breakout': bearish_breakout,
            'bullish_info': bullish_info if bullish_breakout else None,
            'bearish_info': bearish_info if bearish_breakout else None,
            'num_support_zones': len(zones['support']),
            'num_resistance_zones': len(zones['resistance'])
        }

        if bullish_breakout:
            print(f"✅ BULLISH BREAKOUT (broke ${bullish_info['zone_level']:.2f})")
            self.results['bullish_breakouts'].append(result)
        elif bearish_breakout:
            print(f"✅ BEARISH BREAKOUT (broke ${bearish_info['zone_level']:.2f})")
            self.results['bearish_breakouts'].append(result)
        else:
            print("⚪ No breakout")

        return result

    def scan_all(self, max_stocks: int = None, delay: float = 0.5):
        """
        Scan all stocks in the list

        Parameters
        ----------
        max_stocks : int
            Maximum number of stocks to scan (None = all)
        delay : float
            Delay between requests in seconds (to avoid rate limiting)
        """
        stocks_to_scan = self.stocks[:max_stocks] if max_stocks else self.stocks

        print(f"\n{'='*80}")
        print(f"SCANNING {len(stocks_to_scan)} STOCKS FOR SUPPORT/RESISTANCE BREAKOUTS")
        print(f"{'='*80}\n")
        print(f"Parameters:")
        print(f"  - Timeframe: {self.timeframe}")
        print(f"  - Detection Length: {self.detection_length}")
        print(f"  - Lookback Bars: {self.lookback_bars}")
        print(f"  - Min Breakout %: {self.min_breakout_pct}%")
        print(f"  - Period: {self.period}")
        print(f"\n{'='*80}\n")

        for i, symbol in enumerate(stocks_to_scan, 1):
            print(f"[{i}/{len(stocks_to_scan)}] ", end="")
            self.scan_stock(symbol)

            # Rate limiting
            if i < len(stocks_to_scan):
                time.sleep(delay)

        print(f"\n{'='*80}")
        print("SCAN COMPLETE")
        print(f"{'='*80}\n")

    def print_results(self):
        """Print scan results in a formatted table"""
        print("\n" + "="*100)
        print("🚀 BULLISH BREAKOUTS (Broke Above Resistance)")
        print("="*100)

        if not self.results['bullish_breakouts']:
            print("No bullish breakouts found.")
        else:
            print(f"\nFound {len(self.results['bullish_breakouts'])} stocks:\n")
            print(f"{'Symbol':<8} {'Price':<10} {'Broke':<10} {'Breakout %':<12} {'Distance':<12} {'Bars Ago':<10} {'Strength'}")
            print("-" * 100)

            for result in sorted(self.results['bullish_breakouts'],
                                key=lambda x: x['bullish_info']['breakout_pct'], reverse=True):
                info = result['bullish_info']
                strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"

                print(f"{result['symbol']:<8} "
                      f"${result['current_price']:<9.2f} "
                      f"${info['zone_level']:<9.2f} "
                      f"+{info['breakout_pct']:<11.2f}% "
                      f"+{info['distance_pct']:<11.2f}% "
                      f"{info['bars_ago']:<10} "
                      f"{strength}")

        print("\n" + "="*100)
        print("📉 BEARISH BREAKOUTS (Broke Below Support)")
        print("="*100)

        if not self.results['bearish_breakouts']:
            print("No bearish breakouts found.")
        else:
            print(f"\nFound {len(self.results['bearish_breakouts'])} stocks:\n")
            print(f"{'Symbol':<8} {'Price':<10} {'Broke':<10} {'Breakout %':<12} {'Distance':<12} {'Bars Ago':<10} {'Strength'}")
            print("-" * 100)

            for result in sorted(self.results['bearish_breakouts'],
                                key=lambda x: x['bearish_info']['breakout_pct'], reverse=True):
                info = result['bearish_info']
                strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"

                print(f"{result['symbol']:<8} "
                      f"${result['current_price']:<9.2f} "
                      f"${info['zone_level']:<9.2f} "
                      f"-{info['breakout_pct']:<11.2f}% "
                      f"-{info['distance_pct']:<11.2f}% "
                      f"{info['bars_ago']:<10} "
                      f"{strength}")

        print("\n" + "="*100)

    def export_to_csv(self, filename: str = "breakout_results.csv"):
        """Export results to CSV file"""
        all_results = []

        for result in self.results['bullish_breakouts']:
            info = result['bullish_info']
            all_results.append({
                'Symbol': result['symbol'],
                'Type': 'Bullish Breakout',
                'Current_Price': result['current_price'],
                'Zone_Level': info['zone_level'],
                'Breakout_Pct': info['breakout_pct'],
                'Distance_Pct': info['distance_pct'],
                'Bars_Ago': info['bars_ago'],
                'Breakout_Price': info['breakout_close']
            })

        for result in self.results['bearish_breakouts']:
            info = result['bearish_info']
            all_results.append({
                'Symbol': result['symbol'],
                'Type': 'Bearish Breakout',
                'Current_Price': result['current_price'],
                'Zone_Level': info['zone_level'],
                'Breakout_Pct': info['breakout_pct'],
                'Distance_Pct': info['distance_pct'],
                'Bars_Ago': info['bars_ago'],
                'Breakout_Price': info['breakout_close']
            })

        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv(filename, index=False)
            print(f"\n✅ Results exported to {filename}")
        else:
            print("\n⚠️  No results to export")


def quick_breakout_scan(stocks: List[str] = None, lookback_bars: int = 3, max_stocks: int = 20):
    """
    Quick breakout scan function for easy use

    Parameters
    ----------
    stocks : List[str]
        List of stocks to scan (default: first 20 NASDAQ-100)
    lookback_bars : int
        Number of recent bars to check (default: 3)
    max_stocks : int
        Maximum stocks to scan (default: 20)
    """
    scanner = BreakoutScanner(
        stocks=stocks,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=lookback_bars,
        min_breakout_pct=0.5
    )

    scanner.scan_all(max_stocks=max_stocks, delay=0.5)
    scanner.print_results()
    scanner.export_to_csv(f"breakout_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    return scanner


if __name__ == "__main__":
    """
    Example usage
    """

    # Quick scan - first 20 NASDAQ-100 stocks
    print("\n🔍 BREAKOUT SCAN - Top 20 NASDAQ-100 Stocks\n")
    scanner = quick_breakout_scan(max_stocks=20, lookback_bars=3)

    # Full scan example (commented out - takes longer)
    # print("\n🔍 FULL BREAKOUT SCAN - All NASDAQ-100 Stocks\n")
    # scanner = quick_breakout_scan(max_stocks=None, lookback_bars=3)

    # Custom stock list example
    # custom_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMD', 'META']
    # scanner = quick_breakout_scan(stocks=custom_stocks, lookback_bars=3)
