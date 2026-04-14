# Fidelity Sell Call

Sell to close call option positions from current holdings. Uses bid price.

## Instructions

1. Find the fidelity pane ID by title:

```bash
tmux list-panes -a -F "#{pane_id} #{pane_title}" | grep "fidelity" | grep -v "fidelity-mcp" | awk '{print $1}'
```

If no pane found, tell the user to run `/fidelity-pane` first.

2. Send the command to the fidelity pane:

```bash
# Dry run — sell all call positions
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/sell_call.py" Enter

# Dry run — sell a specific position by index
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/sell_call.py --index 0" Enter

# Execute for real
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/sell_call.py --confirm" Enter
```

3. IMPORTANT: Always run as dry run first. Only add --confirm if the user explicitly says to execute.

4. Wait ~30 seconds, then capture the output:

```bash
tmux capture-pane -t <pane_id> -p
```

5. Display the output to the user.
