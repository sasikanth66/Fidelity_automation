"""
Debug INTC to see what's actually happening
"""
import yfinance as yf
import pandas as pd
from support_resistance_indicator import SupportResistanceIndicator

# Download INTC data
print("Downloading INTC data...")
df = yf.download('INTC', period='6mo', interval='1h', progress=False)

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
# Convert columns to lowercase for indicator
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
    print(f"  {i+1}. Level: ${zone.level:.2f} (${zone.bottom:.2f} - ${zone.top:.2f})")

print(f"\nResistance zones found: {len(zones['resistance'])}")
for i, zone in enumerate(zones['resistance'][:5]):
    print(f"  {i+1}. Level: ${zone.level:.2f} (${zone.bottom:.2f} - ${zone.top:.2f})")

# Check if price is above any resistance zones
current_price = df_4h['Close'].iloc[-1]
print(f"\n\nCurrent price: ${current_price:.2f}")
print("\nChecking if current price is above resistance zones:")
for i, zone in enumerate(zones['resistance'][:5]):
    if current_price > zone.top:
        print(f"  ✅ Above resistance {i+1}: ${zone.level:.2f} (zone top: ${zone.top:.2f})")
    else:
        print(f"  ❌ NOT above resistance {i+1}: ${zone.level:.2f} (zone top: ${zone.top:.2f})")
