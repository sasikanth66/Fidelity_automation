#!/usr/bin/env python3
"""
Fidelity MCP Server
Exposes Fidelity account info and trading as MCP tools.
"""
import asyncio
import json
import os
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from fidelity.fidelity import FidelityAutomation

server = Server("fidelity-server")
fidelity = None


def ensure_login():
    """Initialize Fidelity session, reusing saved cookies if possible."""
    global fidelity
    if fidelity is None:
        fidelity = FidelityAutomation(headless=True, title="my_session", save_state=True)

    # Try saved session
    accounts = fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
    if accounts:
        return True

    # Fall back to env var credentials
    username = os.getenv("FIDELITY_USERNAME")
    password = os.getenv("FIDELITY_PASSWORD")
    totp_secret = os.getenv("FIDELITY_TOTP")

    if not username or not password:
        return False

    success, fully_logged_in = fidelity.login(username, password, totp_secret=totp_secret)
    if not success:
        return False
    if not fully_logged_in:
        return False

    fidelity.get_list_of_accounts(set_flag=True, get_withdrawal_bal=True)
    return True


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_accounts",
            description="Get all Fidelity accounts with balances and nicknames.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="get_holdings",
            description="Get stock holdings for a specific account or all accounts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "account_number": {
                        "type": "string",
                        "description": "Account number. Leave empty for all accounts.",
                    }
                },
            },
        ),
        types.Tool(
            name="get_summary",
            description="Get aggregated holdings summary across all accounts.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        types.Tool(
            name="buy_stock",
            description="Buy a stock in a Fidelity account. Defaults to dry run (preview).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "quantity": {"type": "number", "description": "Number of shares"},
                    "account": {"type": "string", "description": "Account number"},
                    "limit_price": {"type": "number", "description": "Limit price (optional, market order if omitted)"},
                    "confirm": {"type": "boolean", "description": "Set to true to execute for real. Default is false (dry run).", "default": False},
                },
                "required": ["ticker", "quantity", "account"],
            },
        ),
        types.Tool(
            name="sell_stock",
            description="Sell a stock in a Fidelity account. Defaults to dry run (preview).",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "Stock ticker symbol"},
                    "quantity": {"type": "number", "description": "Number of shares"},
                    "account": {"type": "string", "description": "Account number"},
                    "limit_price": {"type": "number", "description": "Limit price (optional, market order if omitted)"},
                    "confirm": {"type": "boolean", "description": "Set to true to execute for real. Default is false (dry run).", "default": False},
                },
                "required": ["ticker", "quantity", "account"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    if arguments is None:
        arguments = {}

    try:
        # Run all sync Fidelity calls in a thread to avoid blocking the async loop
        return await asyncio.to_thread(_handle_tool_sync, name, arguments)
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error in {name}: {str(e)}")]


def _handle_tool_sync(name: str, arguments: dict) -> list[types.TextContent]:
    if not ensure_login():
        return [types.TextContent(
            type="text",
            text="Failed to login to Fidelity. Ensure saved session exists or set FIDELITY_USERNAME, FIDELITY_PASSWORD, FIDELITY_TOTP env vars."
        )]

    if name == "get_accounts":
        accounts = fidelity.account_dict
        result = []
        total = 0.0
        for acct_num, info in accounts.items():
            balance = info.get("balance", 0.0)
            total += balance
            result.append(f"Account: {acct_num} ({info.get('nickname', 'N/A')})")
            result.append(f"  Balance: ${balance:,.2f}")
            result.append(f"  Withdrawal Available: ${info.get('withdrawal_balance', 0.0):,.2f}")
            result.append("")
        result.append(f"Total: ${total:,.2f}")
        return [types.TextContent(type="text", text="\n".join(result))]

    elif name == "get_holdings":
        fidelity.getAccountInfo()
        account_number = arguments.get("account_number")

        if account_number:
            stocks = fidelity.get_stocks_in_account(account_number)
            lines = [f"Holdings for {account_number}:"]
            for ticker, qty in stocks.items():
                lines.append(f"  {ticker}: {qty} shares")
            return [types.TextContent(type="text", text="\n".join(lines))]
        else:
            result = []
            for acct_num, info in fidelity.account_dict.items():
                result.append(f"Account: {acct_num} ({info.get('nickname', 'N/A')})")
                if info.get("stocks"):
                    for stock in info["stocks"]:
                        result.append(f"  {stock['ticker']:6s}  {stock['quantity']:>8.2f} shares  @ ${stock['last_price']:>9.2f}  = ${stock['value']:>11.2f}")
                else:
                    result.append("  No holdings")
                result.append("")
            return [types.TextContent(type="text", text="\n".join(result))]

    elif name == "get_summary":
        fidelity.getAccountInfo()
        summary = fidelity.summary_holdings()
        lines = ["Aggregated Holdings:"]
        for ticker, info in summary.items():
            lines.append(f"  {ticker}: {info['quantity']} shares @ ${info['last_price']:.2f} = ${info['value']:.2f}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name in ("buy_stock", "sell_stock"):
        action = "buy" if name == "buy_stock" else "sell"
        ticker = arguments["ticker"]
        quantity = arguments["quantity"]
        account = arguments["account"]
        limit_price = arguments.get("limit_price")
        confirm = arguments.get("confirm", False)
        dry = not confirm

        mode = "DRY RUN" if dry else "LIVE"
        success, error = fidelity.transaction(
            stock=ticker,
            quantity=quantity,
            action=action,
            account=account,
            dry=dry,
            limit_price=limit_price,
        )

        if success:
            return [types.TextContent(
                type="text",
                text=f"[{mode}] {action.upper()} {quantity} {ticker} in {account} — SUCCESS"
            )]
        else:
            return [types.TextContent(
                type="text",
                text=f"[{mode}] {action.upper()} {quantity} {ticker} in {account} — FAILED: {error}"
            )]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="fidelity-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
