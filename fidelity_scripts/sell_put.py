#!/usr/bin/env python3
"""Sell to close put options from current holdings."""
import argparse
import json
import os
from common import get_fidelity, load_config

HOLDINGS_PATH = os.path.join(os.path.dirname(__file__), "current_option_holdings.json")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "buy_put_config.json")

parser = argparse.ArgumentParser()
parser.add_argument("--confirm", action="store_true", help="Execute for real")
parser.add_argument("--index", type=int, default=None, help="Sell a specific put position by index (0-based)")
args = parser.parse_args()

with open(HOLDINGS_PATH) as f:
    holdings = json.load(f)

if not holdings["puts"]:
    print("No put positions to sell.")
    exit(0)

# Show positions
print("Current put positions:")
for i, pos in enumerate(holdings["puts"]):
    print(f"  [{i}] {pos['quantity']}x {pos['ticker']} {pos['expiration']} ${pos['strike']} put in {pos['account']}")
print()

# Determine which to sell
if args.index is not None:
    if args.index >= len(holdings["puts"]):
        print(f"ERROR: Index {args.index} out of range (0-{len(holdings['puts'])-1})")
        exit(1)
    positions_to_sell = [args.index]
else:
    positions_to_sell = list(range(len(holdings["puts"])))

config = load_config(CONFIG_PATH)
headless = config.get("headless", True)
dry = not args.confirm
mode = "DRY RUN" if dry else "LIVE"

fidelity = get_fidelity(headless=headless, skip_account_check=True)

sold_indices = []
for idx in positions_to_sell:
    pos = holdings["puts"][idx]
    print(f"[{mode}] SELL TO CLOSE {pos['quantity']}x {pos['ticker']} {pos['expiration']} ${pos['strike']} put in {pos['account']}")

    success, error = fidelity.option_transaction(
        stock=pos["ticker"],
        expiration=pos["expiration"],
        strike=pos["strike"],
        option_type="put",
        quantity=pos["quantity"],
        action="sell_to_close",
        account=pos["account"],
        dry=dry,
        limit_price=None,
    )

    if success:
        print(f"  Result: SUCCESS")
        if not dry:
            sold_indices.append(idx)
    else:
        print(f"  Result: FAILED — {error}")

# Remove sold positions (reverse order to preserve indices)
if sold_indices:
    for idx in sorted(sold_indices, reverse=True):
        holdings["puts"].pop(idx)
    with open(HOLDINGS_PATH, "w") as f:
        json.dump(holdings, f, indent=2)
        f.write("\n")
    print(f"\nHoldings updated: {len(holdings['calls'])} call(s), {len(holdings['puts'])} put(s)")

fidelity.close_browser()
