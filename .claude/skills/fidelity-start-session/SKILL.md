# Fidelity Start Session

Start the persistent Fidelity trading server. Must be running before any trades.

## Instructions

1. Find the fidelity pane ID by title:

```bash
tmux list-panes -a -F "#{pane_id} #{pane_title}" | grep "fidelity" | grep -v "fidelity-mcp" | awk '{print $1}'
```

If no pane found, tell the user to run `/fidelity-pane` first.

2. Start the trading server:

```bash
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/trading_server.py" Enter
```

3. Wait for the `>` prompt. If it asks for login credentials, the user needs to enter them in the pane.

4. Once running, type commands directly in the pane:
   - `buy_call` — dry run buy call
   - `buy_call --confirm` — live buy call
   - `buy_put` / `buy_put --confirm`
   - `sell_call` / `sell_call --confirm`
   - `sell_put` / `sell_put --confirm`
   - `status` — show current holdings
   - `quit` — stop server

5. Client scripts also work from any other pane via socket.
