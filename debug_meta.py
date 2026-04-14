"""
Debug META to see what's actually happening
"""
import yfinance as yf
import pandas as pd
from support_resistance_indicator import SupportResistanceIndicator

# Download META data
print("Downloading META data...")
df = yf.download('META', period='6mo', interval='1h', progress=False)

# Flatten MultiIndex columns if present
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# Resample to 4H
df_4h = df.resample('4H').agg({
    'Open': 'first',
    'High': 'max',
    'Low': 'min',
    'Close': 'last',
    'Volume': 'sum'
}).dropna()

print(f"\nTotal 4H bars: {len(df_4h)}")
print(f"\nLast 10 bars:")
print(df_4h[['Open', 'High', 'Low', 'Close']].tail(10))

print(f"\nCurrent price: ${df_4h['Close'].iloc[-1]:.2f}")
print(f"\nLowest price in last 20 bars: ${df_4h['Low'].tail(20).min():.2f}")
print(f"Highest price in last 20 bars: ${df_4h['High'].tail(20).max():.2f}")

# Calculate S/R zones
df_4h_lower = df_4h.copy()
df_4h_lower.columns = [col.lower() for col in df_4h_lower.columns]

indicator = SupportResistanceIndicator(
    detection_length=20,
    sr_margin=2.0,
    mn_margin=1.3,
    avoid_false_breakouts=True,
    check_historical_sr=True,
    show_manipulation=True
)

df_signals = indicator.calculate(df_4h_lower)
zones = indicator.get_zones()

print(f"\n\nSupport zones found: {len(zones['support'])}")
for i, zone in enumerate(zones['support'][:5]):
    distance = abs(df_4h['Close'].iloc[-1] - zone.level) / df_4h['Close'].iloc[-1]
    within_20 = "✅" if distance <= 0.20 else "❌"
    print(f"  {i+1}. Level: ${zone.level:.2f} (${zone.bottom:.2f} - ${zone.top:.2f}) - Distance: {distance*100:.1f}% {within_20}")

print(f"\nResistance zones found: {len(zones['resistance'])}")
for i, zone in enumerate(zones['resistance'][:5]):
    distance = abs(df_4h['Close'].iloc[-1] - zone.level) / df_4h['Close'].iloc[-1]
    within_20 = "✅" if distance <= 0.20 else "❌"
    print(f"  {i+1}. Level: ${zone.level:.2f} (${zone.bottom:.2f} - ${zone.top:.2f}) - Distance: {distance*100:.1f}% {within_20}")

# Check if price is below any support zones
current_price = df_4h['Close'].iloc[-1]
print(f"\n\nCurrent price: ${current_price:.2f}")
print("\nChecking if current price is below support zones (within 20%):")
for i, zone in enumerate(zones['support'][:5]):
    distance = abs(current_price - zone.level) / current_price
    if distance <= 0.20:  # Within 20%
        if current_price < zone.bottom:
            print(f"  ✅ Below support {i+1}: ${zone.level:.2f} (zone bottom: ${zone.bottom:.2f})")
        else:
            print(f"  ❌ NOT below support {i+1}: ${zone.level:.2f} (zone bottom: ${zone.bottom:.2f})")

# Check last 5 bars for when price went below support
print(f"\n\nLast 5 bars analysis:")
recent_bars = df_4h.tail(5)
for i, (idx, bar) in enumerate(recent_bars.iterrows()):
    print(f"\nBar {i+1} ({idx}):")
    print(f"  Low: ${bar['Low']:.2f}, Close: ${bar['Close']:.2f}")
    
    # Check if this bar broke below $721.73
    if bar['Low'] < 721.73:
        print(f"  ⚠️  Low touched below $721.73")
    if bar['Close'] < 721.73:
        print(f"  ⚠️  Closed below $721.73")
