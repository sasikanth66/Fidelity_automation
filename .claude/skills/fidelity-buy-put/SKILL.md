# Fidelity Buy Put

Buy to open a put option using config with dynamic OTM strike and expiration.

## Instructions

1. Find the fidelity pane ID by title:

```bash
tmux list-panes -a -F "#{pane_id} #{pane_title}" | grep "fidelity" | grep -v "fidelity-mcp" | awk '{print $1}'
```

If no pane found, tell the user to run `/fidelity-pane` first.

2. Config is at `/Users/sasi/stock_sr_scanner/fidelity_scripts/buy_put_config.json`. If the user wants to change ticker, quantity, account, expiration_days, or headless — edit the config first.

3. Send the command to the fidelity pane:

```bash
# Dry run (default)
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/buy_put.py" Enter

# Override ticker
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/buy_put.py --ticker AAPL" Enter

# Execute for real
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/buy_put.py --confirm" Enter
```

4. IMPORTANT: Always run as dry run first. Only add --confirm if the user explicitly says to execute.

5. Wait ~30 seconds, then capture the output:

```bash
tmux capture-pane -t <pane_id> -p
```

6. Display the output to the user.
