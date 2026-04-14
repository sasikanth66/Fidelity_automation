"""
S&P 500 Stock List
Fetches current S&P 500 constituents
"""

import pandas as pd
import requests
from io import StringIO

def get_sp500_tickers():
    """
    Fetch S&P 500 tickers from Wikipedia
    
    Returns
    -------
    list
        List of S&P 500 ticker symbols
    """
    try:
        # Read S&P 500 list from Wikipedia with proper headers
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        
        # Add headers to avoid 403 error
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        tables = pd.read_html(StringIO(response.text))
        sp500_table = tables[0]
        
        # Get ticker symbols and clean them
        tickers = sp500_table['Symbol'].tolist()
        
        # Replace special characters that yfinance doesn't like
        tickers = [ticker.replace('.', '-') for ticker in tickers]
        
        print(f"✅ Fetched {len(tickers)} S&P 500 stocks")
        return tickers
    
    except Exception as e:
        print(f"❌ Error fetching S&P 500 list: {e}")
        print("Using fallback list of major S&P 500 stocks...")
        
        # Fallback list of major S&P 500 stocks
        return [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK-B', 'UNH', 'JNJ',
            'V', 'XOM', 'WMT', 'JPM', 'PG', 'MA', 'CVX', 'HD', 'LLY', 'MRK',
            'ABBV', 'PEP', 'KO', 'AVGO', 'COST', 'MCD', 'TMO', 'CSCO', 'ACN', 'ABT',
            'WFC', 'DHR', 'VZ', 'ADBE', 'CRM', 'NFLX', 'NKE', 'TXN', 'PM', 'DIS',
            'CMCSA', 'UPS', 'NEE', 'RTX', 'ORCL', 'INTC', 'AMD', 'QCOM', 'HON', 'UNP'
        ]

# Pre-fetch the list
SP500_STOCKS = get_sp500_tickers()

if __name__ == "__main__":
    print(f"\nS&P 500 Stocks ({len(SP500_STOCKS)} total):")
    print(", ".join(SP500_STOCKS[:20]) + "...")
