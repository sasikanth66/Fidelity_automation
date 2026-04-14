"""
Stock Scanner for Support/Resistance Bounces
Scans a list of stocks to find ones that recently bounced off S&R levels
"""

import pandas as pd
import yfinance as yf
from datetime import datetime
import time
from typing import List, Dict, Tuple
from support_resistance_indicator import SupportResistanceIndicator
import warnings
warnings.filterwarnings('ignore')


# NASDAQ-100 stocks (major components - you can expand this list)
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


class SupportResistanceScanner:
    """
    Scanner to identify stocks bouncing off support or resistance levels

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
        Number of recent bars to check for bounces (default: 3)
    """

    def __init__(
        self,
        stocks: List[str] = None,
        period: str = "6mo",
        interval: str = "1h",
        timeframe: str = "4H",
        detection_length: int = 20,
        lookback_bars: int = 3
    ):
        self.stocks = stocks or NASDAQ_100
        self.period = period
        self.interval = interval
        self.timeframe = timeframe
        self.detection_length = detection_length
        self.lookback_bars = lookback_bars

        self.results = {
            'support_bounces': [],
            'resistance_bounces': []
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

    def check_support_bounce(self, df: pd.DataFrame, zones: List) -> Tuple[bool, Dict]:
        """
        Check if stock recently bounced off support

        A support bounce occurs when:
        1. Price touches/penetrates support zone
        2. Price bounces back above support
        3. Zone is within 20% of current price
        4. Bounce happened within lookback period

        Returns
        -------
        Tuple[bool, Dict]
            (bounce_detected, bounce_info)
        """
        if len(zones) == 0 or len(df) < self.lookback_bars:
            return False, {}
        
        current_price = df['close'].iloc[-1]

        # Check most recent support zones
        for zone in zones[:3]:  # Check latest 3 support zones
            # Filter out zones too far from current price (>20% away)
            distance_from_current = abs(current_price - zone.level) / current_price
            if distance_from_current > 0.20:
                continue
            
            # Look at last N bars
            recent_bars = df.tail(self.lookback_bars)

            for i in range(len(recent_bars)):
                bar = recent_bars.iloc[i]

                # Check if price touched or went below support zone
                touched_support = bar['low'] <= zone.top and bar['low'] >= zone.bottom * 0.99

                if touched_support:
                    # Check if price bounced (closed above support)
                    bounced = bar['close'] > zone.bottom

                    # Check if subsequent bars show bullish follow-through
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
                                'current_price': current_price,
                                'distance_pct': ((current_price - zone.level) / zone.level) * 100
                            }

        return False, {}

    def check_resistance_bounce(self, df: pd.DataFrame, zones: List) -> Tuple[bool, Dict]:
        """
        Check if stock recently bounced off resistance

        A resistance bounce occurs when:
        1. Price touches/penetrates resistance zone
        2. Price bounces back below resistance
        3. Zone is within 20% of current price
        4. Bounce happened within lookback period

        Returns
        -------
        Tuple[bool, Dict]
            (bounce_detected, bounce_info)
        """
        if len(zones) == 0 or len(df) < self.lookback_bars:
            return False, {}
        
        current_price = df['close'].iloc[-1]

        # Check most recent resistance zones
        for zone in zones[:3]:  # Check latest 3 resistance zones
            # Filter out zones too far from current price (>20% away)
            distance_from_current = abs(current_price - zone.level) / current_price
            if distance_from_current > 0.20:
                continue
            
            # Look at last N bars
            recent_bars = df.tail(self.lookback_bars)

            for i in range(len(recent_bars)):
                bar = recent_bars.iloc[i]

                # Check if price touched or went above resistance zone
                touched_resistance = bar['high'] >= zone.bottom and bar['high'] <= zone.top * 1.01

                if touched_resistance:
                    # Check if price bounced (closed below resistance)
                    bounced = bar['close'] < zone.top

                    # Check if subsequent bars show bearish follow-through
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
                                'current_price': current_price,
                                'distance_pct': ((zone.level - current_price) / zone.level) * 100
                            }

        return False, {}

    def scan_stock(self, symbol: str) -> Dict:
        """Scan a single stock for bounces"""
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
        
        current_price = df['close'].iloc[-1]
        
        # Flip zones based on breakouts
        # When price breaks above resistance, it becomes support
        # When price breaks below support, it becomes resistance
        actual_support_zones = []
        actual_resistance_zones = []
        
        # Process resistance zones
        for zone in zones['resistance']:
            # Filter out zones too far from current price (>20%)
            distance = abs(current_price - zone.level) / current_price
            if distance > 0.20:
                continue
            
            if current_price > zone.top:
                # Price broke above resistance → flip to support
                # Old resistance top becomes new support bottom
                # Old resistance bottom becomes new support top
                from support_resistance_indicator import SnR
                flipped_zone = SnR(
                    left=zone.left,
                    right=zone.right,
                    top=zone.top,      # Old resistance top is new support top
                    bottom=zone.bottom, # Old resistance bottom is new support bottom
                    level=zone.bottom,  # Support level is at the bottom of flipped zone
                    is_resistance=False,
                    m=zone.m
                )
                actual_support_zones.append(flipped_zone)
            else:
                # Price still below resistance → keep as resistance
                actual_resistance_zones.append(zone)
        
        # Process support zones
        for zone in zones['support']:
            # Filter out zones too far from current price (>20%)
            distance = abs(current_price - zone.level) / current_price
            if distance > 0.20:
                continue
            
            if current_price < zone.bottom:
                # Price broke below support → flip to resistance
                # Old support bottom becomes new resistance top
                # Old support top becomes new resistance bottom
                from support_resistance_indicator import SnR
                flipped_zone = SnR(
                    left=zone.left,
                    right=zone.right,
                    top=zone.top,      # Old support top is new resistance top
                    bottom=zone.bottom, # Old support bottom is new resistance bottom
                    level=zone.top,     # Resistance level is at the top of flipped zone
                    is_resistance=True,
                    m=zone.m
                )
                actual_resistance_zones.append(flipped_zone)
            else:
                # Price still above support → keep as support
                actual_support_zones.append(zone)

        # Check for bounces with flipped zones
        support_bounce, support_info = self.check_support_bounce(df_signals, actual_support_zones)
        resistance_bounce, resistance_info = self.check_resistance_bounce(df_signals, actual_resistance_zones)

        result = {
            'symbol': symbol,
            'current_price': current_price,
            'support_bounce': support_bounce,
            'resistance_bounce': resistance_bounce,
            'support_info': support_info if support_bounce else None,
            'resistance_info': resistance_info if resistance_bounce else None,
            'num_support_zones': len(actual_support_zones),
            'num_resistance_zones': len(actual_resistance_zones)
        }

        if support_bounce:
            print(f"✅ SUPPORT BOUNCE (${support_info['zone_level']:.2f})")
            self.results['support_bounces'].append(result)
        elif resistance_bounce:
            print(f"✅ RESISTANCE BOUNCE (${resistance_info['zone_level']:.2f})")
            self.results['resistance_bounces'].append(result)
        else:
            print("⚪ No bounce")

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
        print(f"SCANNING {len(stocks_to_scan)} STOCKS FOR SUPPORT/RESISTANCE BOUNCES")
        print(f"{'='*80}\n")
        print(f"Parameters:")
        print(f"  - Timeframe: {self.timeframe}")
        print(f"  - Detection Length: {self.detection_length}")
        print(f"  - Lookback Bars: {self.lookback_bars}")
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

    def export_to_csv(self, filename: str = "bounce_results.csv"):
        """Export results to CSV file"""
        all_results = []

        for result in self.results['support_bounces']:
            info = result['support_info']
            all_results.append({
                'Symbol': result['symbol'],
                'Type': 'Support Bounce',
                'Current_Price': result['current_price'],
                'Zone_Level': info['zone_level'],
                'Distance_Pct': info['distance_pct'],
                'Bars_Ago': info['bars_ago'],
                'Touch_Price': info['touch_price'],
                'Bounce_Close': info['bounce_close']
            })

        for result in self.results['resistance_bounces']:
            info = result['resistance_info']
            all_results.append({
                'Symbol': result['symbol'],
                'Type': 'Resistance Bounce',
                'Current_Price': result['current_price'],
                'Zone_Level': info['zone_level'],
                'Distance_Pct': info['distance_pct'],
                'Bars_Ago': info['bars_ago'],
                'Touch_Price': info['touch_price'],
                'Bounce_Close': info['bounce_close']
            })

        if all_results:
            df = pd.DataFrame(all_results)
            df.to_csv(filename, index=False)
            print(f"\n✅ Results exported to {filename}")
        else:
            print("\n⚠️  No results to export")


def quick_scan(stocks: List[str] = None, lookback_bars: int = 3, max_stocks: int = 20):
    """
    Quick scan function for easy use

    Parameters
    ----------
    stocks : List[str]
        List of stocks to scan (default: first 20 NASDAQ-100)
    lookback_bars : int
        Number of recent bars to check (default: 3)
    max_stocks : int
        Maximum stocks to scan (default: 20)
    """
    scanner = SupportResistanceScanner(
        stocks=stocks,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=lookback_bars
    )

    scanner.scan_all(max_stocks=max_stocks, delay=0.5)
    scanner.print_results()
    scanner.export_to_csv(f"bounce_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    return scanner


if __name__ == "__main__":
    """
    Example usage
    """

    # Quick scan - first 20 NASDAQ-100 stocks
    print("\n🔍 QUICK SCAN - Top 20 NASDAQ-100 Stocks\n")
    scanner = quick_scan(max_stocks=20, lookback_bars=3)

    # Full scan example (commented out - takes longer)
    # print("\n🔍 FULL SCAN - All NASDAQ-100 Stocks\n")
    # scanner = quick_scan(max_stocks=None, lookback_bars=3)

    # Custom stock list example
    # custom_stocks = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA', 'AMD', 'META']
    # scanner = quick_scan(stocks=custom_stocks, lookback_bars=3)
