"""Flask web UI for Fidelity Trading Server."""
from flask import Flask, request, jsonify, Response
import json
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# These get set by trading_server.py before starting
handle_command_fn = None

app = Flask(__name__)

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fidelity Trading</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 20px; }
  h1 { color: #00d4aa; margin-bottom: 20px; font-size: 1.5rem; }
  h2 { color: #888; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
  .card { background: #16213e; border-radius: 10px; padding: 20px; border: 1px solid #0f3460; }

  .config-row { display: flex; gap: 10px; margin-bottom: 8px; align-items: center; }
  .config-row label { width: 120px; font-size: 0.85rem; color: #aaa; flex-shrink: 0; }
  .config-row input, .config-row select { flex: 1; background: #1a1a2e; border: 1px solid #0f3460; color: #e0e0e0; padding: 6px 10px; border-radius: 5px; font-size: 0.85rem; }
  .config-row input:focus, .config-row select:focus { outline: none; border-color: #00d4aa; }

  .btn { padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: opacity 0.2s; }
  .btn:hover { opacity: 0.85; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
  .btn-save { background: #0f3460; color: #00d4aa; }
  .btn-buy-dry { background: #1b4332; color: #95d5b2; }
  .btn-buy-live { background: #2d6a4f; color: #fff; }
  .btn-sell-dry { background: #542323; color: #f4a0a0; }
  .btn-sell-live { background: #7c2d2d; color: #fff; }
  .btn-info { background: #0f3460; color: #a8dadc; }
  .btn-danger { background: #7c2d2d; color: #fff; }

  .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }

  .output { background: #0d1117; border: 1px solid #0f3460; border-radius: 10px; padding: 15px; min-height: 200px; max-height: 500px; overflow-y: auto; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8rem; line-height: 1.6; white-space: pre-wrap; }
  .output .timestamp { color: #555; }
  .output .success { color: #00d4aa; }
  .output .error { color: #ff6b6b; }
  .output .info { color: #a8dadc; }

  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid #555; border-top-color: #00d4aa; border-radius: 50%; animation: spin 0.8s linear infinite; margin-left: 8px; vertical-align: middle; }
  @keyframes spin { to { transform: rotate(360deg); } }

  .status-bar { display: flex; gap: 15px; margin-bottom: 20px; }
  .status-item { background: #16213e; padding: 10px 15px; border-radius: 8px; border: 1px solid #0f3460; }
  .status-item .label { font-size: 0.7rem; color: #888; text-transform: uppercase; }
  .status-item .value { font-size: 1.1rem; color: #00d4aa; font-weight: 600; }
</style>
</head>
<body>

<h1>Fidelity Trading Dashboard</h1>

<div class="status-bar" id="status-bar">
  <div class="status-item"><div class="label">Server</div><div class="value" id="server-status">Connected</div></div>
  <div class="status-item"><div class="label">Calls</div><div class="value" id="call-count">0</div></div>
  <div class="status-item"><div class="label">Puts</div><div class="value" id="put-count">0</div></div>
</div>

<!-- TradingView Chart -->
<div class="card" style="margin-bottom:20px; padding:0; overflow:hidden;">
  <div id="tradingview-widget" style="height:500px;"></div>
</div>
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script>
function loadChart(symbol) {
  document.getElementById('tradingview-widget').innerHTML = '';
  new TradingView.widget({
    "autosize": true,
    "symbol": symbol || "SPY",
    "interval": "5",
    "timezone": "America/New_York",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#16213e",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "container_id": "tradingview-widget"
  });
}
</script>

<div class="grid">
  <div class="card">
    <h2>Buy Call Config</h2>
    <div class="config-row"><label>Ticker</label><input id="bc-ticker" value="SPY"></div>
    <div class="config-row"><label>Account</label><input id="bc-account" value="Z09522470"></div>
    <div class="config-row"><label>Quantity</label><input id="bc-quantity" type="number" value="1"></div>
    <div class="config-row"><label>Exp Days</label><input id="bc-expdays" type="number" value="1"></div>
    <div class="config-row"><label>Limit Price</label>
      <select id="bc-limit"><option value="ask">Ask</option><option value="mid">Mid</option><option value="bid">Bid</option></select>
    </div>
    <div style="margin-top:10px"><button class="btn btn-save" onclick="saveConfig('buy_call')">Save Config</button></div>
  </div>

  <div class="card">
    <h2>Buy Put Config</h2>
    <div class="config-row"><label>Ticker</label><input id="bp-ticker" value="SPY"></div>
    <div class="config-row"><label>Account</label><input id="bp-account" value="Z09522470"></div>
    <div class="config-row"><label>Quantity</label><input id="bp-quantity" type="number" value="1"></div>
    <div class="config-row"><label>Exp Days</label><input id="bp-expdays" type="number" value="1"></div>
    <div class="config-row"><label>Limit Price</label>
      <select id="bp-limit"><option value="ask">Ask</option><option value="mid">Mid</option><option value="bid">Bid</option></select>
    </div>
    <div style="margin-top:10px"><button class="btn btn-save" onclick="saveConfig('buy_put')">Save Config</button></div>
  </div>
</div>

<div class="actions">
  <button class="btn btn-buy-dry" onclick="sendCmd('buy_call', true)">Buy Call (Dry)</button>
  <button class="btn btn-buy-live" onclick="confirmAndSend('buy_call')">Buy Call (Live)</button>
  <button class="btn btn-buy-dry" onclick="sendCmd('buy_put', true)">Buy Put (Dry)</button>
  <button class="btn btn-buy-live" onclick="confirmAndSend('buy_put')">Buy Put (Live)</button>
  <button class="btn btn-sell-dry" onclick="sendCmd('sell_call', true)">Sell Call (Dry)</button>
  <button class="btn btn-sell-live" onclick="confirmAndSend('sell_call')">Sell Call (Live)</button>
  <button class="btn btn-sell-dry" onclick="sendCmd('sell_put', true)">Sell Put (Dry)</button>
  <button class="btn btn-sell-live" onclick="confirmAndSend('sell_put')">Sell Put (Live)</button>
  <button class="btn btn-info" onclick="sendCmd('status', true)">Status</button>
  <button class="btn btn-info" onclick="sendCmd('accounts', true)">Accounts</button>
  <button class="btn btn-info" onclick="sendCmd('holdings', true)">Holdings</button>
</div>

<h2>Output</h2>
<div class="output" id="output"></div>

<script>
const output = document.getElementById('output');

function loadChart(symbol) {
  document.getElementById('tradingview-widget').innerHTML = '';
  new TradingView.widget({
    "autosize": true,
    "symbol": symbol || "SPY",
    "interval": "5",
    "timezone": "America/New_York",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "toolbar_bg": "#16213e",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "container_id": "tradingview-widget"
  });
}

function log(text, cls='info') {
  const ts = new Date().toLocaleTimeString();
  output.innerHTML += `<span class="timestamp">[${ts}]</span> <span class="${cls}">${text}</span>\\n`;
  output.scrollTop = output.scrollHeight;
}

function clearOutput() { output.innerHTML = ''; }

async function sendCmd(action, dry) {
  log(`Sending: ${action} (${dry ? 'dry run' : 'LIVE'})...`);
  const btns = document.querySelectorAll('.btn');
  btns.forEach(b => b.disabled = true);

  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action, dry})
    });
    const data = await res.json();
    formatResult(data);
    refreshStatus();
  } catch(e) {
    log('Error: ' + e.message, 'error');
  } finally {
    btns.forEach(b => b.disabled = false);
  }
}

function confirmAndSend(action) {
  if (confirm(`Execute ${action.replace('_',' ').toUpperCase()} for REAL?`)) {
    sendCmd(action, false);
  }
}

function formatResult(data) {
  if (data.message) log(data.message, data.success ? 'success' : 'info');
  if (data.current_price) log(`  Price: $${data.current_price.toFixed(2)}  Exp: ${data.expiration}  Strike: $${data.strike}`);
  if (data.success === true) log('  Result: SUCCESS', 'success');
  if (data.success === false && data.error) log('  Result: FAILED - ' + data.error, 'error');
  if (data.error && data.success === undefined && !data.results) log('Error: ' + data.error, 'error');

  if (data.results) {
    data.results.forEach(r => {
      log(r.message, r.success ? 'success' : 'error');
      if (r.success) log('  Result: SUCCESS', 'success');
      else if (r.error) log('  Result: FAILED - ' + r.error, 'error');
    });
  }

  if (data.accounts && data.total !== undefined) {
    data.accounts.forEach(a => log(`  ${a.account} (${a.nickname})  Balance: $${a.balance.toLocaleString()}  Withdrawal: $${a.withdrawal.toLocaleString()}`));
    log(`  Total: $${data.total.toLocaleString()}`, 'success');
  } else if (data.accounts) {
    data.accounts.forEach(a => {
      log(`  ${a.account} (${a.nickname})`);
      if (a.stocks) a.stocks.forEach(s => log(`    ${s.ticker}  ${s.quantity} shares @ $${s.last_price} = $${s.value}`));
    });
  }

  if (data.options_from_fidelity) {
    if (data.options_from_fidelity.length) {
      log('  Option Positions (Fidelity):');
      data.options_from_fidelity.forEach(o => log(`    ${o.account}  ${o.symbol}  ${o.quantity} contracts @ $${o.last_price} = $${o.value}`));
    } else {
      log('  No option positions on Fidelity.');
    }
    const local = data.local_holdings || {};
    const calls = local.calls || [];
    const puts = local.puts || [];
    log(`  Local: ${calls.length} call(s), ${puts.length} put(s)`);
    calls.forEach((c,i) => log(`    [${i}] ${c.quantity}x ${c.ticker} ${c.expiration} $${c.strike} call`));
    puts.forEach((p,i) => log(`    [${i}] ${p.quantity}x ${p.ticker} ${p.expiration} $${p.strike} put`));
  }

  if (data.holdings && !data.calls) {
    Object.entries(data.holdings).forEach(([t, info]) => log(`  ${t}: ${info.quantity} @ $${info.last_price} = $${info.value}`));
  }
}

async function loadConfigs() {
  try {
    const bc = await (await fetch('/api/config/buy_call')).json();
    document.getElementById('bc-ticker').value = bc.ticker || 'SPY';
    document.getElementById('bc-account').value = bc.account || '';
    document.getElementById('bc-quantity').value = bc.quantity || 1;
    document.getElementById('bc-expdays').value = bc.expiration_days || 1;
    document.getElementById('bc-limit').value = bc.limit_price || 'ask';
    loadChart(bc.ticker || 'SPY');
  } catch(e) {}
  try {
    const bp = await (await fetch('/api/config/buy_put')).json();
    document.getElementById('bp-ticker').value = bp.ticker || 'SPY';
    document.getElementById('bp-account').value = bp.account || '';
    document.getElementById('bp-quantity').value = bp.quantity || 1;
    document.getElementById('bp-expdays').value = bp.expiration_days || 1;
    document.getElementById('bp-limit').value = bp.limit_price || 'ask';
  } catch(e) {}
}

async function saveConfig(type) {
  const prefix = type === 'buy_call' ? 'bc' : 'bp';
  const config = {
    ticker: document.getElementById(prefix + '-ticker').value,
    account: document.getElementById(prefix + '-account').value,
    quantity: parseInt(document.getElementById(prefix + '-quantity').value),
    expiration_days: parseInt(document.getElementById(prefix + '-expdays').value),
    limit_price: document.getElementById(prefix + '-limit').value,
    strike_mode: "nearest_otm",
    headless: true
  };
  try {
    await fetch('/api/config/' + type, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(config)
    });
    log(`${type} config saved.`, 'success');
  } catch(e) {
    log('Error saving config: ' + e.message, 'error');
  }
}

async function refreshStatus() {
  try {
    const res = await fetch('/api/command', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({action: 'local_status'})
    });
    const data = await res.json();
    document.getElementById('call-count').textContent = (data.calls || []).length;
    document.getElementById('put-count').textContent = (data.puts || []).length;
  } catch(e) {}
}

loadConfigs();
refreshStatus();
</script>
</body>
</html>"""


@app.route('/')
def dashboard():
    return Response(DASHBOARD_HTML, content_type='text/html')


@app.route('/api/command', methods=['POST'])
def api_command():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400

    # Special local-only command for UI status bar
    if data.get("action") == "local_status":
        holdings_path = os.path.join(SCRIPTS_DIR, "current_option_holdings.json")
        try:
            with open(holdings_path) as f:
                return jsonify(json.load(f))
        except:
            return jsonify({"calls": [], "puts": []})

    if handle_command_fn is None:
        return jsonify({"error": "Trading server not initialized"}), 503

    result = handle_command_fn(json.dumps(data))
    try:
        return jsonify(json.loads(result))
    except:
        return jsonify({"error": result})


@app.route('/api/config/<name>', methods=['GET'])
def get_config(name):
    config_map = {
        "buy_call": "buy_call_config.json",
        "buy_put": "buy_put_config.json",
        "server": "server_config.json",
    }
    filename = config_map.get(name)
    if not filename:
        return jsonify({"error": f"Unknown config: {name}"}), 404
    path = os.path.join(SCRIPTS_DIR, filename)
    try:
        with open(path) as f:
            return jsonify(json.load(f))
    except FileNotFoundError:
        return jsonify({"error": "Config not found"}), 404


@app.route('/api/config/<name>', methods=['POST'])
def save_config(name):
    config_map = {
        "buy_call": "buy_call_config.json",
        "buy_put": "buy_put_config.json",
        "server": "server_config.json",
    }
    filename = config_map.get(name)
    if not filename:
        return jsonify({"error": f"Unknown config: {name}"}), 404
    path = os.path.join(SCRIPTS_DIR, filename)
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON body"}), 400
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    return jsonify({"success": True})


def start_web_ui(command_fn, port=5555):
    """Start Flask in a background thread."""
    global handle_command_fn
    handle_command_fn = command_fn
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
