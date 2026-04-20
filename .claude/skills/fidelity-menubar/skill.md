# Fidelity Menu Bar

Launch the Fidelity Trade menu bar app for quick-access trading buttons.

## Instructions

1. First check if FidelityTrade is already running:

```bash
pgrep -f FidelityTrade
```

2. If it is NOT running, launch it in the background:

```bash
/Users/sasi/stock_sr_scanner/fidelity_scripts/FidelityTrade.app/Contents/MacOS/FidelityTrade &
```

3. If it is already running, tell the user the menu bar app is already active.

4. Confirm to the user that the Fidelity Trade menu bar app is ready. Remind them they can click "$ Trade" in the menu bar for Buy/Sell Call/Put buttons, Status, and Start Server.
