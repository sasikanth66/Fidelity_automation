#!/usr/bin/env python3
"""Test Fidelity automation using Chrome instead of Firefox."""
from playwright.sync_api import sync_playwright
import json, os

PROFILE_PATH = "/Users/sasi/stock_sr_scanner/Fidelity_my_session.json"
FIDELITY_URL = "https://digital.fidelity.com/ftgw/digital/portfolio/summary"

print("Launching Chrome via Playwright...")
pw = sync_playwright().start()
browser = pw.chromium.launch(
    headless=False,
)

# Load existing session cookies if available
storage = PROFILE_PATH if os.path.exists(PROFILE_PATH) else None
context = browser.new_context(storage_state=storage)
page = context.new_page()

print(f"Navigating to Fidelity portfolio page...")
page.goto(FIDELITY_URL, wait_until="domcontentloaded", timeout=30000)
page.wait_for_timeout(5000)

url = page.url
title = page.title()
print(f"  URL:   {url}")
print(f"  Title: {title}")

if "summary" in url.lower() or "portfolio" in url.lower():
    print("\nChrome works! Session is valid and Fidelity loaded.")
else:
    print("\nRedirected (likely to login). Session may not transfer across browsers.")
    print("You may need to re-login with Chrome.")

input("\nPress Enter to close the browser...")
browser.close()
pw.stop()
