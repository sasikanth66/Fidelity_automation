#!/usr/bin/env python3
"""Reset current option holdings to 0,0."""
import json
import os

HOLDINGS_PATH = os.path.join(os.path.dirname(__file__), "current_option_holdings.json")

holdings = {"calls": [], "puts": []}
with open(HOLDINGS_PATH, "w") as f:
    json.dump(holdings, f, indent=2)
    f.write("\n")

print("Option holdings reset:")
print(f"  Calls: {len(holdings['calls'])} positions")
print(f"  Puts:  {len(holdings['puts'])} positions")
