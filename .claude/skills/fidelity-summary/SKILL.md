# Fidelity Summary

Get aggregated holdings summary across all accounts.

## Instructions

1. Find the fidelity pane ID by title:

```bash
tmux list-panes -a -F "#{pane_id} #{pane_title}" | grep "fidelity" | awk '{print $1}'
```

If no pane found, tell the user to run `/fidelity-pane` first.

2. Send the command to the fidelity pane:

```bash
tmux send-keys -t <pane_id> "python /Users/sasi/stock_sr_scanner/fidelity_scripts/get_summary.py" Enter
```

3. Wait ~20 seconds for the script to run (it uses Playwright), then capture the output:

```bash
tmux capture-pane -t <pane_id> -p
```

4. Display the output to the user. If there's a login error, tell the user to run `python fidelity_balance.py` with `headless=False` first to establish a session.
