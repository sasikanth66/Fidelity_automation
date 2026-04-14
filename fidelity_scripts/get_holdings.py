#!/usr/bin/env python3
"""Get stock holdings for a specific account or all accounts."""
import sys
from common import get_fidelity

fidelity = get_fidelity()
fidelity.getAccountInfo()

account_number = sys.argv[1] if len(sys.argv) > 1 else None

if account_number:
    stocks = fidelity.get_stocks_in_account(account_number)
    print(f"\n=== Holdings for {account_number} ===\n")
    for ticker, qty in stocks.items():
        print(f"  {ticker}: {qty} shares")
else:
    print("\n=== All Account Holdings ===\n")
    for acct_num, info in fidelity.account_dict.items():
        print(f"Account: {acct_num} ({info.get('nickname', 'N/A')})")
        if info.get("stocks"):
            for stock in info["stocks"]:
                print(f"  {stock['ticker']:6s}  {stock['quantity']:>8.2f} shares  @ ${stock['last_price']:>9.2f}  = ${stock['value']:>11.2f}")
        else:
            print("  No holdings")
        print()

fidelity.close_browser()
