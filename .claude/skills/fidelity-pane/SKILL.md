# Fidelity Pane

Create a dedicated side pane for running Fidelity scripts.

## Instructions

1. First check if a tmux pane titled 'fidelity' already exists:

```bash
tmux list-panes -a -F "#{pane_id} #{pane_title}" | grep "fidelity"
```

2. If it does NOT exist, split the current window horizontally to create a side pane:

```bash
tmux split-window -h -d -P -F "#{pane_id}" "cd /Users/sasi/stock_sr_scanner/fidelity_scripts && exec zsh"
```

Then name the new pane using the pane_id returned above:

```bash
tmux select-pane -t <pane_id> -T fidelity
```

3. If it already exists, tell the user the fidelity pane is already running.

4. Confirm to the user that the fidelity side pane is ready.
