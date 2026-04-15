#!/usr/bin/env python3
"""
Fidelity Trading Server — persistent browser session for fast trades.
Start once, send commands via Unix socket.
"""
import json
import os
import queue
import signal
import socket
import sys
import threading
import time
from datetime import datetime, timedelta

import yfinance as yf
from fidelity.fidelity import FidelityAutomation

SOCKET_PATH = "/tmp/fidelity_trading.sock"
PROFILE_PATH = "/Users/sasi/stock_sr_scanner"
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
HOLDINGS_PATH = os.path.join(SCRIPTS_DIR, "current_option_holdings.json")

fidelity = None
command_queue = queue.Queue()
result_map = {}
result_lock = threading.Lock()
result_events = {}


def load_config(name):
    path = os.path.join(SCRIPTS_DIR, name)
    with open(path) as f:
        return json.load(f)


def load_holdings():
    with open(HOLDINGS_PATH) as f:
        return json.load(f)


def save_holdings(holdings):
    with open(HOLDINGS_PATH, "w") as f:
        json.dump(holdings, f, indent=2)
        f.write("\n")


def get_current_price(ticker):
    t = yf.Ticker(ticker)
    hist = t.history(period="1d")
    if hist.empty:
        raise ValueError(f"Could not get price for {ticker}")
    return float(hist["Close"].iloc[-1])


def resolve_expiration(ticker, days_out):
    t = yf.Ticker(ticker)
    expirations = t.options
    target = datetime.now() + timedelta(days=days_out)
    target_str = target.strftime("%Y-%m-%d")
    for exp in sorted(expirations):
        if exp >= target_str:
            return exp
    return expirations[-1] if expirations else None


def find_nearest_otm_strike(ticker, expiration, option_type, current_price):
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


def handle_buy(option_type, dry=True):
    config_name = f"buy_{option_type}_config.json"
    config = load_config(config_name)

    ticker = config["ticker"]
    quantity = config["quantity"]
    account = config["account"]
    limit_price = config.get("limit_price", "ask")

    current_price = get_current_price(ticker)
    expiration = resolve_expiration(ticker, config["expiration_days"])
    if not expiration:
        return {"success": False, "error": "No valid expirations found"}

    strike = find_nearest_otm_strike(ticker, expiration, option_type, current_price)

    mode = "DRY RUN" if dry else "LIVE"
    msg = f"[{mode}] BUY TO OPEN {quantity}x {ticker} {expiration} ${strike} {option_type} in {account}"

    success, error = fidelity.option_transaction(
        stock=ticker,
        expiration=expiration,
        strike=strike,
        option_type=option_type,
        quantity=quantity,
        action="buy_to_open",
        account=account,
        dry=dry,
        limit_price=limit_price,
    )

    if success and not dry:
        holdings = load_holdings()
        holdings[f"{option_type}s"].append({
            "ticker": ticker,
            "expiration": expiration,
            "strike": strike,
            "quantity": quantity,
            "account": account,
            "limit_price": str(limit_price),
        })
        save_holdings(holdings)

    return {
        "success": success,
        "error": error,
        "message": msg,
        "current_price": current_price,
        "expiration": expiration,
        "strike": strike,
    }


def handle_sell(option_type, dry=True, index=None):
    holdings = load_holdings()
    key = f"{option_type}s"

    if not holdings[key]:
        return {"success": False, "error": f"No {option_type} positions to sell"}

    if index is not None and index >= len(holdings[key]):
        return {"success": False, "error": f"Index {index} out of range (0-{len(holdings[key])-1})"}

    positions = [index] if index is not None else list(range(len(holdings[key])))
    results = []
    sold_indices = []
    mode = "DRY RUN" if dry else "LIVE"

    for idx in positions:
        pos = holdings[key][idx]
        msg = f"[{mode}] SELL TO CLOSE {pos['quantity']}x {pos['ticker']} {pos['expiration']} ${pos['strike']} {option_type} in {pos['account']}"

        success, error = fidelity.option_transaction(
            stock=pos["ticker"],
            expiration=pos["expiration"],
            strike=pos["strike"],
            option_type=option_type,
            quantity=pos["quantity"],
            action="sell_to_close",
            account=pos["account"],
            dry=dry,
            limit_price=None,
        )

        results.append({"message": msg, "success": success, "error": error})
        if success and not dry:
            sold_indices.append(idx)

    if sold_indices:
        for idx in sorted(sold_indices, reverse=True):
            holdings[key].pop(idx)
        save_holdings(holdings)

    return {"results": results, "holdings": holdings}


def handle_accounts():
    fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
    result = {"accounts": []}
    total = 0.0
    for acct_num, info in fidelity.account_dict.items():
        balance = info.get("balance", 0.0)
        total += balance
        result["accounts"].append({
            "account": acct_num,
            "nickname": info.get("nickname", "N/A"),
            "balance": balance,
            "withdrawal": info.get("withdrawal_balance", 0.0),
        })
    result["total"] = total
    return result


def handle_holdings():
    fidelity.getAccountInfo()
    result = {"accounts": []}
    for acct_num, info in fidelity.account_dict.items():
        acct = {"account": acct_num, "nickname": info.get("nickname", "N/A"), "stocks": []}
        if info.get("stocks"):
            for stock in info["stocks"]:
                acct["stocks"].append(stock)
        result["accounts"].append(acct)
    return result


def handle_summary():
    fidelity.getAccountInfo()
    summary = fidelity.summary_holdings()
    return {"holdings": {t: dict(info) for t, info in summary.items()}}


def handle_status():
    """Show option holdings from Fidelity with current P/L."""
    # Get fresh positions from Fidelity
    fidelity.getAccountInfo()

    options = []
    for acct_num, info in fidelity.account_dict.items():
        if not info.get("stocks"):
            continue
        for stock in info["stocks"]:
            ticker = stock.get("ticker", "")
            # Options have symbols starting with - like -SPY260417C687
            if ticker.startswith("-"):
                options.append({
                    "account": acct_num,
                    "symbol": ticker,
                    "quantity": stock.get("quantity", 0),
                    "last_price": stock.get("last_price", 0),
                    "value": stock.get("value", 0),
                })

    # Also show local holdings tracker
    local = load_holdings()

    return {"options_from_fidelity": options, "local_holdings": local}


def handle_command(data):
    try:
        cmd = json.loads(data)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON"})

    action = cmd.get("action", "")
    dry = cmd.get("dry", True)
    index = cmd.get("index")

    try:
        if action == "buy_call":
            result = handle_buy("call", dry=dry)
        elif action == "buy_put":
            result = handle_buy("put", dry=dry)
        elif action == "sell_call":
            result = handle_sell("call", dry=dry, index=index)
        elif action == "sell_put":
            result = handle_sell("put", dry=dry, index=index)
        elif action == "status":
            result = handle_status()
        elif action == "accounts":
            result = handle_accounts()
        elif action == "holdings":
            result = handle_holdings()
        elif action == "summary":
            result = handle_summary()
        elif action == "quit":
            return "QUIT"
        else:
            result = {"error": f"Unknown action: {action}"}
    except Exception as e:
        result = {"error": str(e)}

    return json.dumps(result, default=str)


def print_result(result):
    """Pretty print a command result."""
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except:
            print(result)
            return

    if "message" in result:
        print(result["message"])
    if "current_price" in result:
        print(f"  Current price: ${result['current_price']:.2f}")
        print(f"  Expiration: {result['expiration']}")
        print(f"  Strike: ${result['strike']}")
    if "success" in result:
        if result["success"]:
            print("  Result: SUCCESS")
        elif result.get("error"):
            print(f"  Result: FAILED — {result['error']}")
    if "results" in result:
        for r in result["results"]:
            print(r["message"])
            if r.get("success"):
                print("  Result: SUCCESS")
            elif r.get("error"):
                print(f"  Result: FAILED — {r['error']}")
    if "accounts" in result and "total" in result:
        for a in result["accounts"]:
            print(f"  {a['account']} ({a['nickname']})")
            print(f"    Balance: ${a['balance']:,.2f}  |  Withdrawal: ${a['withdrawal']:,.2f}")
        print(f"  Total: ${result['total']:,.2f}")
    elif "accounts" in result:
        for a in result["accounts"]:
            print(f"  {a['account']} ({a['nickname']})")
            if a.get("stocks"):
                for s in a["stocks"]:
                    print(f"    {s['ticker']:6s}  {s['quantity']:>8.2f} shares  @ ${s['last_price']:>9.2f}  = ${s['value']:>11.2f}")
            else:
                print("    No holdings")
    elif "holdings" in result and "calls" not in result:
        for ticker, info in result["holdings"].items():
            print(f"  {ticker}: {info['quantity']} shares @ ${info['last_price']:.2f} = ${info['value']:.2f}")
    if "options_from_fidelity" in result:
        opts = result["options_from_fidelity"]
        local = result.get("local_holdings", {})
        if opts:
            print("  Option Positions (from Fidelity):")
            for o in opts:
                print(f"    {o['account']}  {o['symbol']}  {o['quantity']} contracts  @ ${o['last_price']:.2f}  = ${o['value']:.2f}")
        else:
            print("  No option positions found on Fidelity.")
        print()
        calls = local.get("calls", [])
        puts = local.get("puts", [])
        print(f"  Local Tracker: {len(calls)} call(s), {len(puts)} put(s)")
        for i, c in enumerate(calls):
            print(f"    [{i}] {c['quantity']}x {c['ticker']} {c['expiration']} ${c['strike']} call")
        for i, p in enumerate(puts):
            print(f"    [{i}] {p['quantity']}x {p['ticker']} {p['expiration']} ${p['strike']} put")
    elif "calls" in result and "puts" in result:
        print(f"  Calls: {len(result['calls'])} position(s)")
        for i, c in enumerate(result['calls']):
            print(f"    [{i}] {c['quantity']}x {c['ticker']} {c['expiration']} ${c['strike']} call")
        print(f"  Puts: {len(result['puts'])} position(s)")
        for i, p in enumerate(result['puts']):
            print(f"    [{i}] {p['quantity']}x {p['ticker']} {p['expiration']} ${p['strike']} put")
    if "error" in result and "success" not in result and "results" not in result and "calls" not in result:
        print(f"Error: {result['error']}")


ALIASES = {
    "bc": ("buy_call", False),
    "bcd": ("buy_call", True),
    "bp": ("buy_put", False),
    "bpd": ("buy_put", True),
    "sc": ("sell_call", False),
    "scd": ("sell_call", True),
    "sp": ("sell_put", False),
    "spd": ("sell_put", True),
}


def parse_stdin_command(line):
    """Parse a simple stdin command into a JSON command dict."""
    parts = line.strip().split()
    if not parts:
        return None

    action = parts[0].lower()

    # Check aliases
    if action in ALIASES:
        real_action, dry = ALIASES[action]
        cmd = {"action": real_action, "dry": dry}
    else:
        cmd = {"action": action, "dry": True}
        for i, p in enumerate(parts[1:]):
            if p == "--confirm":
                cmd["dry"] = False

    # Parse --index for any command
    for i, p in enumerate(parts[1:]):
        if p == "--index" and i + 1 < len(parts[1:]):
            try:
                cmd["index"] = int(parts[i + 2])
            except (ValueError, IndexError):
                pass

    return cmd


HELP_TEXT = """----------------------------------------
Commands:
  bc / bcd              Buy call (live / dry run)
  bp / bpd              Buy put (live / dry run)
  sc / scd              Sell calls (live / dry run)
  sp / spd              Sell puts (live / dry run)
  status                Show option holdings
  accounts              Show account balances
  holdings              Show stock positions
  summary               Aggregated holdings
  quit                  Stop server
----------------------------------------"""


def handle_command_threadsafe(data):
    """Queue a command and wait for the main thread to process it."""
    request_id = id(threading.current_thread()) + id(data)
    event = threading.Event()
    with result_lock:
        result_events[request_id] = event
    command_queue.put((request_id, data))
    event.wait(timeout=120)
    with result_lock:
        result = result_map.pop(request_id, json.dumps({"error": "Timeout"}))
        result_events.pop(request_id, None)
    return result


def process_queue():
    """Process one pending command from the queue (called from main thread)."""
    try:
        request_id, data = command_queue.get_nowait()
        response = handle_command(data)
        with result_lock:
            result_map[request_id] = response
            if request_id in result_events:
                result_events[request_id].set()
    except queue.Empty:
        pass


def cleanup(signum=None, frame=None):
    global fidelity
    print("\nShutting down...")
    if fidelity:
        try:
            fidelity.close_browser()
        except:
            pass
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)
    sys.exit(0)


def socket_listener(sock):
    """Handle socket connections in a thread."""
    while True:
        try:
            conn, _ = sock.accept()
            data = conn.recv(4096).decode("utf-8")
            if not data:
                conn.close()
                continue
            response = handle_command_threadsafe(data)
            if response == "QUIT":
                conn.sendall(json.dumps({"message": "Server shutting down"}).encode("utf-8"))
                conn.close()
                break
            conn.sendall(response.encode("utf-8"))
            conn.close()
        except Exception:
            pass


def main():
    global fidelity

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    headless = True
    try:
        cfg = load_config("server_config.json")
        headless = cfg.get("headless", True)
    except:
        pass

    print("Starting Fidelity browser...")
    fidelity = FidelityAutomation(headless=headless, title="my_session", save_state=True, profile_path=PROFILE_PATH)

    accounts = fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
    if not accounts:
        print("Session expired. Logging in...")
        username = os.environ.get("FIDELITY_USERNAME") or input("Username: ")
        import getpass
        password = os.environ.get("FIDELITY_PASSWORD") or getpass.getpass("Password: ")
        totp_secret = os.environ.get("FIDELITY_TOTP")

        success, fully_logged_in = fidelity.login(username, password, totp_secret=totp_secret)
        if not success:
            print("Login failed.")
            cleanup()
        if not fully_logged_in:
            code = input("Enter 2FA code: ")
            if not fidelity.login_2FA(code):
                print("2FA failed.")
                cleanup()
        print("Logged in successfully.")
    else:
        print("Session valid. Logged in.")

    # Start socket listener in background thread for client scripts
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(SOCKET_PATH)
    sock.listen(1)
    thread = threading.Thread(target=socket_listener, args=(sock,), daemon=True)
    thread.start()

    # Start web UI in background thread (uses threadsafe wrapper)
    from web_ui import start_web_ui
    web_port = 5555
    web_thread = threading.Thread(target=start_web_ui, args=(handle_command_threadsafe, web_port), daemon=True)
    web_thread.start()

    # Auto-open in browser
    import webbrowser
    webbrowser.open(f"http://localhost:{web_port}")

    print(f"\nTrading server ready.")
    print(f"  Socket: {SOCKET_PATH}")
    print(f"  Web UI: http://localhost:{web_port}")
    print(HELP_TEXT)

    # REPL loop — also processes queued commands from web/socket
    import select
    while True:
        # Process any pending web/socket commands
        process_queue()

        # Check if stdin has input (non-blocking)
        try:
            if select.select([sys.stdin], [], [], 0.1)[0]:
                line = sys.stdin.readline()
                if not line:
                    break
                line = line.strip()
                if not line:
                    continue
                cmd = parse_stdin_command(line)
                if not cmd:
                    continue
                if cmd["action"] == "quit":
                    break
                response = handle_command(json.dumps(cmd))
                try:
                    result = json.loads(response)
                except:
                    result = {"error": response}
                print_result(result)
                print(HELP_TEXT)
                print("> ", end="", flush=True)
        except (EOFError, KeyboardInterrupt):
            break

    cleanup()


if __name__ == "__main__":
    main()
