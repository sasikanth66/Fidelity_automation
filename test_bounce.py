"""
Test the fixed bounce scanner on NASDAQ top 20
"""
from stock_scanner import SupportResistanceScanner

# NASDAQ Top 20
NASDAQ_TOP_20 = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 
    'META', 'TSLA', 'AVGO', 'COST', 'NFLX',
    'AMD', 'PEP', 'ADBE', 'CSCO', 'TMUS',
    'CMCSA', 'INTC', 'TXN', 'QCOM', 'AMGN'
]

print("\n🔍 Testing Fixed Bounce Scanner - NASDAQ Top 20\n")

scanner = SupportResistanceScanner(
    stocks=NASDAQ_TOP_20,
    period="6mo",
    interval="1h",
    timeframe="4H",
    detection_length=20,
    lookback_bars=5
)

scanner.scan_all(max_stocks=None, delay=0.5)
scanner.print_results()

print(f"\n📊 Summary:")
print(f"  Support bounces (bullish): {len(scanner.results['support_bounces'])}")
print(f"  Resistance bounces (bearish): {len(scanner.results['resistance_bounces'])}")
print(f"  Total: {len(scanner.results['support_bounces']) + len(scanner.results['resistance_bounces'])}")
