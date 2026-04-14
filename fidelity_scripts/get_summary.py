#!/usr/bin/env python3
"""Get aggregated holdings summary across all accounts."""
from common import get_fidelity

fidelity = get_fidelity()
fidelity.getAccountInfo()
summary = fidelity.summary_holdings()

print("\n=== Aggregated Holdings ===\n")
for ticker, info in summary.items():
    print(f"  {ticker}: {info['quantity']} shares @ ${info['last_price']:.2f} = ${info['value']:.2f}")

fidelity.close_browser()
