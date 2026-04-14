#!/usr/bin/env python3
"""Get all Fidelity accounts with balances."""
from common import get_fidelity

fidelity = get_fidelity()

print("\n=== Fidelity Accounts ===\n")
total = 0.0
for acct_num, info in fidelity.account_dict.items():
    balance = info.get("balance", 0.0)
    total += balance
    print(f"Account: {acct_num} ({info.get('nickname', 'N/A')})")
    print(f"  Balance: ${balance:,.2f}")
    print(f"  Withdrawal Available: ${info.get('withdrawal_balance', 0.0):,.2f}")
    print()

print(f"Total: ${total:,.2f}")
fidelity.close_browser()
