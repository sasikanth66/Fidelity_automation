#!/usr/bin/env python3
"""Login to Fidelity and save session cookies. Run this when session expires."""
from fidelity.fidelity import FidelityAutomation

PROFILE_PATH = "/Users/sasi/stock_sr_scanner"

fidelity = FidelityAutomation(headless=False, title="my_session", save_state=True, profile_path=PROFILE_PATH)

# Try existing session first
accounts = fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
if accounts:
    print("Session is still valid. No login needed.")
    fidelity.close_browser()
    exit(0)

# Need to login
import os, getpass
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

print("Login successful. Session saved.")
fidelity.close_browser()
