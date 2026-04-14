"""Shared Fidelity helpers — login, price resolution, strike/expiration logic."""
import json
import os
from datetime import datetime, timedelta
import yfinance as yf
from fidelity.fidelity import FidelityAutomation


PROFILE_PATH = "/Users/sasi/stock_sr_scanner"


def get_fidelity(headless=True, skip_account_check=False):
    """Return a logged-in FidelityAutomation instance."""
    fidelity = FidelityAutomation(headless=headless, title="my_session", save_state=True, profile_path=PROFILE_PATH)
    if skip_account_check:
        return fidelity
    accounts = fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
    if accounts:
        return fidelity

    username = os.getenv("FIDELITY_USERNAME")
    password = os.getenv("FIDELITY_PASSWORD")
    totp_secret = os.getenv("FIDELITY_TOTP")

    if not username or not password:
        print("No saved session and no credentials in env vars.")
        print("Run: python fidelity_balance.py (with headless=False) to establish a session first.")
        fidelity.close_browser()
        exit(1)

    success, fully_logged_in = fidelity.login(username, password, totp_secret=totp_secret)
    if not success or not fully_logged_in:
        print("Login failed.")
        fidelity.close_browser()
        exit(1)

    fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
    return fidelity


def load_config(path):
    with open(path) as f:
        return json.load(f)


def get_current_price(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    if hist.empty:
        raise ValueError(f"Could not get price for {ticker}")
    return float(hist["Close"].iloc[-1])


def resolve_expiration(ticker, days_out):
    """Find the nearest valid option expiration >= today + days_out."""
    t = yf.Ticker(ticker)
    expirations = t.options
    target = datetime.now() + timedelta(days=days_out)
    target_str = target.strftime("%Y-%m-%d")

    for exp in sorted(expirations):
        if exp >= target_str:
            return exp

    return expirations[-1] if expirations else None


def find_nearest_otm_strike(ticker, expiration, option_type, current_price):
    """Find nearest OTM strike. Calls: smallest strike > price. Puts: largest strike < price."""
    t = yf.Ticker(ticker)
    chain = t.option_chain(expiration)

    if option_type == "call":
        strikes = sorted(chain.calls["strike"].unique())
        otm = [s for s in strikes if s > current_price]
        return otm[0] if otm else strikes[-1]
    else:
        strikes = sorted(chain.puts["strike"].unique())
        otm = [s for s in strikes if s < current_price]
        return otm[-1] if otm else strikes[0]
