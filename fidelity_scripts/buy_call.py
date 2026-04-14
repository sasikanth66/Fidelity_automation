#!/usr/bin/env python3
"""Buy to open a call option using config with dynamic strike/expiration."""
import argparse
import json
import os
from common import load_config, get_current_price, resolve_expiration, find_nearest_otm_strike, get_fidelity

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "buy_call_config.json")
HOLDINGS_PATH = os.path.join(os.path.dirname(__file__), "current_option_holdings.json")

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=CONFIG_PATH, help="Path to config JSON")
parser.add_argument("--confirm", action="store_true", help="Execute for real")
parser.add_argument("--ticker", help="Override ticker")
parser.add_argument("--quantity", type=int, help="Override quantity")
parser.add_argument("--account", help="Override account")
args = parser.parse_args()

config = load_config(args.config)
ticker = args.ticker or config["ticker"]
quantity = args.quantity or config["quantity"]
account = args.account or config["account"]
limit_price = config.get("limit_price", "ask")

print(f"Fetching current price for {ticker}...")
current_price = get_current_price(ticker)
print(f"Current price: ${current_price:.2f}")

print(f"Finding expiration >= {config['expiration_days']} days out...")
expiration = resolve_expiration(ticker, config["expiration_days"])
if not expiration:
    print("ERROR: No valid expirations found")
    exit(1)
print(f"Expiration: {expiration}")

print(f"Finding nearest OTM call strike...")
strike = find_nearest_otm_strike(ticker, expiration, "call", current_price)
print(f"Strike: ${strike:.2f}")

dry = not args.confirm
mode = "DRY RUN" if dry else "LIVE"
print(f"\n[{mode}] BUY TO OPEN {quantity}x {ticker} {expiration} ${strike} call in {account}")
if limit_price:
    print(f"Limit: {limit_price}")
print()

headless = config.get("headless", True)
fidelity = get_fidelity(headless=headless, skip_account_check=True)
success, error = fidelity.option_transaction(
    stock=ticker,
    expiration=expiration,
    strike=strike,
    option_type="call",
    quantity=quantity,
    action="buy_to_open",
    account=account,
    dry=dry,
    limit_price=limit_price,
)

if success:
    print("Result: SUCCESS")
    if not dry:
        with open(HOLDINGS_PATH) as f:
            holdings = json.load(f)
        holdings["calls"].append({
            "ticker": ticker,
            "expiration": expiration,
            "strike": strike,
            "quantity": quantity,
            "account": account,
            "limit_price": str(limit_price),
        })
        with open(HOLDINGS_PATH, "w") as f:
            json.dump(holdings, f, indent=2)
            f.write("\n")
        print(f"Holdings updated: {len(holdings['calls'])} call(s), {len(holdings['puts'])} put(s)")
else:
    print(f"Result: FAILED — {error}")

fidelity.close_browser()
