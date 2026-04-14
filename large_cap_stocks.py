"""
Large Cap Stocks (Market Cap > $10B)
Fetches stocks with market cap greater than $10 billion
"""

import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def get_market_cap(symbol):
    """
    Get market cap for a single stock
    
    Returns
    -------
    tuple
        (symbol, market_cap) or (symbol, None) if error
    """
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        market_cap = info.get('marketCap', 0)
        return (symbol, market_cap)
    except:
        return (symbol, None)

def get_large_cap_stocks(min_market_cap=10_000_000_000):
    """
    Fetch all stocks with market cap > $10B
    
    Parameters
    ----------
    min_market_cap : int
        Minimum market cap in dollars (default: $10B)
    
    Returns
    -------
    list
        List of stock symbols with market cap > min_market_cap
    """
    print(f"Fetching large cap stocks (market cap > ${min_market_cap/1e9:.0f}B)...")
    
    try:
        # Start with S&P 500 as base
        from sp500_stocks import get_sp500_tickers
        sp500 = get_sp500_tickers()
        
        # Add NASDAQ 100
        nasdaq100_url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
        import requests
        from io import StringIO
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(nasdaq100_url, headers=headers)
            tables = pd.read_html(StringIO(response.text))
            nasdaq100 = tables[4]['Ticker'].tolist()
        except:
            nasdaq100 = []
        
        # Combine and deduplicate
        all_symbols = list(set(sp500 + nasdaq100))
        print(f"Checking market cap for {len(all_symbols)} stocks...")
        
        # Fetch market caps in parallel
        large_cap_stocks = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(get_market_cap, symbol): symbol for symbol in all_symbols}
            
            completed = 0
            for future in as_completed(futures):
                symbol, market_cap = future.result()
                completed += 1
                
                if completed % 50 == 0:
                    print(f"  Checked {completed}/{len(all_symbols)} stocks...")
                
                if market_cap and market_cap >= min_market_cap:
                    large_cap_stocks.append(symbol)
        
        large_cap_stocks.sort()
        print(f"✅ Found {len(large_cap_stocks)} stocks with market cap > ${min_market_cap/1e9:.0f}B")
        
        return large_cap_stocks
    
    except Exception as e:
        print(f"❌ Error fetching large cap stocks: {e}")
        print("Using S&P 500 as fallback...")
        from sp500_stocks import SP500_STOCKS
        return SP500_STOCKS

# Fetch the list on import
LARGE_CAP_STOCKS = get_large_cap_stocks()

if __name__ == "__main__":
    print(f"\nLarge Cap Stocks ({len(LARGE_CAP_STOCKS)} total):")
    print(", ".join(LARGE_CAP_STOCKS[:30]) + "...")
    
    # Save to file for future use
    with open('large_cap_stocks_list.txt', 'w') as f:
        for symbol in LARGE_CAP_STOCKS:
            f.write(f"{symbol}\n")
    print(f"\n✅ Saved to large_cap_stocks_list.txt")
