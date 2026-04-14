"""
Fetch trending news for large-cap stocks via yfinance.
Outputs JSON to stdout: {symbol: [{headline, publisher, published_at, summary}, ...]}
Only includes stocks with news published within the last 72 hours.
"""

import json
import sys
import time
from datetime import datetime, timezone, timedelta

import yfinance as yf


def load_symbols():
    """Load symbols from large_cap_stocks_list.txt, fall back to NASDAQ_100 from stock_scanner."""
    try:
        with open('large_cap_stocks_list.txt', 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        if symbols:
            return symbols
    except FileNotFoundError:
        pass

    # Fallback: use NASDAQ_100 list from stock_scanner (no network calls)
    from stock_scanner import NASDAQ_100
    return NASDAQ_100


def fetch_news_for_symbol(symbol: str, cutoff: datetime) -> list:
    """
    Fetch recent news for a single symbol.
    Returns list of dicts with headline, publisher, published_at, summary.
    Handles both yfinance v1.0 (nested content) and older flat formats.
    """
    try:
        ticker = yf.Ticker(symbol)
        raw_news = ticker.news
        if not raw_news:
            return []

        articles = []
        for item in raw_news:
            # yfinance v1.0: fields are nested under 'content'
            content = item.get('content', item)

            # Parse publication date
            pub_date_str = content.get('pubDate') or content.get('displayTime', '')
            if pub_date_str:
                try:
                    pub_dt = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                except ValueError:
                    continue
            else:
                # Fallback: old format used Unix timestamp
                pub_ts = item.get('providerPublishTime', 0)
                if pub_ts == 0:
                    continue
                pub_dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc)

            if pub_dt < cutoff:
                continue

            headline = content.get('title', item.get('title', ''))
            summary = content.get('summary', item.get('summary', ''))
            publisher = (
                content.get('provider', {}).get('displayName', '')
                or item.get('publisher', '')
            )

            articles.append({
                'headline': headline,
                'publisher': publisher,
                'published_at': pub_dt.isoformat(),
                'summary': summary,
            })

        return articles

    except Exception:
        return []


def main():
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=72)

    symbols = load_symbols()
    print(f"Scanning {len(symbols)} symbols for news since {cutoff.strftime('%Y-%m-%d %H:%M UTC')}...", file=sys.stderr)

    results = {}
    checked = 0

    for symbol in symbols:
        articles = fetch_news_for_symbol(symbol, cutoff)
        if articles:
            results[symbol] = articles
            print(f"  [{checked+1:3}/{len(symbols)}] {symbol:6} {len(articles)} articles", file=sys.stderr)
        else:
            print(f"  [{checked+1:3}/{len(symbols)}] {symbol:6} no news", file=sys.stderr)

        checked += 1
        if checked % 50 == 0:
            print(f"  --- {checked}/{len(symbols)} checked, {len(results)} with news so far ---", file=sys.stderr)

        time.sleep(0.2)

    print(f"Done. Found news for {len(results)} symbols.", file=sys.stderr)

    # Output JSON to stdout
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
