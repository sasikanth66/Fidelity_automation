"""
Fetch stocks with market cap above a certain threshold
Uses yfinance to get market cap data
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import time

def get_stocks_by_market_cap(min_market_cap_billions=10, max_stocks=500):
    """
    Get list of stocks with market cap above threshold
    
    Parameters
    ----------
    min_market_cap_billions : float
        Minimum market cap in billions (default: 10)
    max_stocks : int
        Maximum number of stocks to return (default: 500)
    
    Returns
    -------
    list
        List of stock symbols meeting the criteria
    """
    
    print(f"\n🔍 Fetching stocks with market cap > ${min_market_cap_billions}B...\n")
    
    # Start with a comprehensive list of major US stocks
    # We'll use S&P 500, NASDAQ-100, and other major indices
    
    # S&P 500 stocks (major US companies)
    sp500_url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    try:
        sp500_table = pd.read_html(sp500_url)[0]
        sp500_symbols = sp500_table['Symbol'].str.replace('.', '-').tolist()
        print(f"✅ Loaded {len(sp500_symbols)} S&P 500 stocks")
    except Exception as e:
        print(f"⚠️  Could not load S&P 500 list: {e}")
        sp500_symbols = []
    
    # NASDAQ-100 stocks (tech-heavy)
    nasdaq100 = [
        'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'ASML',
        'COST', 'NFLX', 'AMD', 'PEP', 'ADBE', 'CSCO', 'TMUS', 'CMCSA', 'INTC', 'TXN',
        'AMGN', 'INTU', 'HON', 'AMAT', 'SBUX', 'ISRG', 'BKNG', 'VRTX', 'ADP', 'GILD',
        'ADI', 'REGN', 'MU', 'LRCX', 'PANW', 'MDLZ', 'PYPL', 'KLAC', 'SNPS', 'CDNS',
        'MELI', 'CRWD', 'MAR', 'MRVL', 'CSX', 'ORLY', 'ADSK', 'FTNT', 'DASH', 'ABNB',
        'NXPI', 'WDAY', 'CPRT', 'CHTR', 'MNST', 'AEP', 'PAYX', 'ROST', 'ODFL', 'FAST',
        'BKR', 'KDP', 'EA', 'VRSK', 'CTSH', 'GEHC', 'DXCM', 'EXC', 'CTAS', 'IDXX',
        'LULU', 'KHC', 'PCAR', 'ZS', 'BIIB', 'CCEP', 'TTWO', 'TEAM', 'ILMN', 'ANSS',
        'XEL', 'FANG', 'WBD', 'CSGP', 'ON', 'DLTR', 'CDW', 'DDOG', 'MDB', 'GFS',
        'WBA', 'MRNA', 'EBAY', 'ZM', 'ENPH', 'SMCI', 'ALGN', 'RIVN', 'LCID', 'ARM'
    ]
    
    # Combine and deduplicate
    all_symbols = list(set(sp500_symbols + nasdaq100))
    print(f"📊 Total unique symbols to check: {len(all_symbols)}")
    
    # Filter by market cap
    qualified_stocks = []
    min_market_cap = min_market_cap_billions * 1e9  # Convert to actual number
    
    print(f"\n⏳ Checking market caps (this may take a few minutes)...\n")
    
    for i, symbol in enumerate(all_symbols):
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            market_cap = info.get('marketCap', 0)
            
            if market_cap >= min_market_cap:
                qualified_stocks.append({
                    'symbol': symbol,
                    'market_cap': market_cap,
                    'name': info.get('shortName', symbol)
                })
                print(f"[{i+1}/{len(all_symbols)}] ✅ {symbol}: ${market_cap/1e9:.1f}B")
            else:
                print(f"[{i+1}/{len(all_symbols)}] ⚪ {symbol}: ${market_cap/1e9:.1f}B (below threshold)")
            
            # Rate limiting
            if (i + 1) % 10 == 0:
                time.sleep(1)  # Pause every 10 requests
                
        except Exception as e:
            print(f"[{i+1}/{len(all_symbols)}] ❌ {symbol}: Error - {str(e)[:50]}")
            continue
        
        # Limit to max_stocks
        if len(qualified_stocks) >= max_stocks:
            print(f"\n⚠️  Reached maximum of {max_stocks} stocks, stopping search.")
            break
    
    # Sort by market cap (largest first)
    qualified_stocks.sort(key=lambda x: x['market_cap'], reverse=True)
    
    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'stocks_marketcap_{min_market_cap_billions}B_{timestamp}.csv'
    
    df = pd.DataFrame(qualified_stocks)
    df['market_cap_billions'] = df['market_cap'] / 1e9
    df = df[['symbol', 'name', 'market_cap_billions']]
    df.to_csv(filename, index=False)
    
    print(f"\n✅ Found {len(qualified_stocks)} stocks with market cap > ${min_market_cap_billions}B")
    print(f"📄 Saved to: {filename}\n")
    
    # Return just the symbols
    return [stock['symbol'] for stock in qualified_stocks]


if __name__ == "__main__":
    # Get stocks with market cap > $10B
    symbols = get_stocks_by_market_cap(min_market_cap_billions=10, max_stocks=500)
    
    print("\n" + "="*80)
    print(f"FINAL LIST: {len(symbols)} stocks")
    print("="*80)
    print(", ".join(symbols[:50]))  # Show first 50
    if len(symbols) > 50:
        print(f"... and {len(symbols) - 50} more")
