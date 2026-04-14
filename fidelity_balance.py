from fidelity.fidelity import FidelityAutomation
import os, getpass

fidelity = FidelityAutomation(headless=False, title="my_session", save_state=True, profile_path="/Users/sasi/stock_sr_scanner")

# Try to access accounts directly (uses saved cookies)
accounts = fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)

# If no accounts returned, session expired — need to login
if not accounts:
    print("Session expired or no saved session. Logging in...")
    username = os.getenv("FIDELITY_USERNAME") or input("Username: ")
    password = os.getenv("FIDELITY_PASSWORD") or getpass.getpass("Password: ")
    totp_secret = os.getenv("FIDELITY_TOTP") or None

    success, fully_logged_in = fidelity.login(username, password, totp_secret=totp_secret)
    if not success:
        print("Login failed.")
        fidelity.close_browser()
        exit(1)
    if not fully_logged_in:
        code = input("Enter 2FA code from SMS: ")
        if not fidelity.login_2FA(code):
            print("2FA failed.")
            fidelity.close_browser()
            exit(1)

    fidelity.get_list_of_accounts(get_withdrawal_bal=True)

# Get detailed holdings
fidelity.getAccountInfo()

# Display
print("\n=== Fidelity Account Summary ===\n")
total = 0.0
for acct_num, info in fidelity.account_dict.items():
    balance = info.get("balance", 0.0)
    total += balance
    print(f"Account: {acct_num} ({info.get('nickname', 'N/A')})")
    print(f"  Balance: ${balance:,.2f}")
    print(f"  Withdrawal Available: ${info.get('withdrawal_balance', 0.0):,.2f}")
    if info.get("stocks"):
        print("  Holdings:")
        for stock in info["stocks"]:
            print(f"    {stock['ticker']:6s}  {stock['quantity']:>8.2f} shares  "
                  f"@ ${stock['last_price']:>9.2f}  = ${stock['value']:>11.2f}")
    print()

print(f"Total across all accounts: ${total:,.2f}")
fidelity.close_browser()
