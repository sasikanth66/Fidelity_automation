"""
Parallel Proximity Scanner - Fast scanning with multiprocessing
Scans custom watchlist on 30-minute timeframe for intraday analysis
"""

from datetime import datetime
from stock_scanner import SupportResistanceScanner
from breakout_scanner import BreakoutScanner
from multiprocessing import Pool, cpu_count
import yfinance as yf
from support_resistance_indicator import SupportResistanceIndicator
import pandas as pd

# Custom watchlist
WATCHLIST = [
    'AAPL', 'NVDA', 'MSFT', 'RKLB', 'ASTS', 'AVGO', 'TSLA', 'MU', 'SNDK', 'META',
    'AMZN', 'HOOD', 'APLD', 'TSM', 'SPY', 'QQQ', 'SMH', 'QCOM', 'LLY', 'MSTR',
    'COIN', 'TGT', 'ANF', 'CRM', 'SOUN', 'LULU', 'PLTR', 'ASML', 'AMD', 'GOOG'
]

def scan_single_stock(args):
    """
    Scan a single stock for breakouts and S/R levels
    
    Parameters
    ----------
    args : tuple
        (symbol, period, interval, timeframe, detection_length, lookback_bars, min_breakout_pct)
    
    Returns
    -------
    dict
        Stock data with breakout and S/R information
    """
    symbol, period, interval, timeframe, detection_length, lookback_bars, min_breakout_pct = args
    
    try:
        # Download data
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty or len(df) < detection_length * 2:
            return None
        
        # Prepare data
        df.columns = df.columns.str.lower()
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # Resample if needed
        if timeframe != interval:
            df = df.resample(timeframe).agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        if len(df) < detection_length * 2:
            return None
        
        # Calculate S&R zones
        indicator = SupportResistanceIndicator(
            detection_length=detection_length,
            sr_margin=2.0,
            mn_margin=1.3,
            avoid_false_breakouts=True,
            check_historical_sr=True,
            show_manipulation=True
        )
        
        df_signals = indicator.calculate(df)
        zones = indicator.get_zones()
        current_price = df['close'].iloc[-1]
        
        # Check for breakouts
        from breakout_scanner import BreakoutScanner
        scanner = BreakoutScanner(stocks=[], period=period, interval=interval, timeframe=timeframe)
        
        bullish_breakout, bullish_info = scanner.check_bullish_breakout(df_signals, zones['resistance'])
        bearish_breakout, bearish_info = scanner.check_bearish_breakout(df_signals, zones['support'])
        
        # Find nearest support (below current price) and resistance (above current price)
        # Flip zones based on price position: resistance above price becomes support, support below price becomes resistance
        
        support_candidates = []
        resistance_candidates = []
        
        # Check support zones
        for zone in zones['support']:
            if zone.level < current_price:
                # Support below price - still support
                support_candidates.append(zone)
            else:
                # Support above price - acts as resistance (price broke below)
                resistance_candidates.append(zone)
        
        # Check resistance zones  
        for zone in zones['resistance']:
            if zone.level > current_price:
                # Resistance above price - still resistance
                resistance_candidates.append(zone)
            else:
                # Resistance below price - acts as support (price broke above)
                support_candidates.append(zone)
        
        # Find nearest by distance
        support_level = None
        if support_candidates:
            nearest_support = min(support_candidates, key=lambda z: abs(z.level - current_price))
            support_level = nearest_support.level
        
        resistance_level = None
        if resistance_candidates:
            nearest_resistance = min(resistance_candidates, key=lambda z: abs(z.level - current_price))
            resistance_level = nearest_resistance.level
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'support': support_level,
            'resistance': resistance_level,
            'bullish_breakout': bullish_breakout,
            'bearish_breakout': bearish_breakout,
            'bullish_info': bullish_info if bullish_breakout else None,
            'bearish_info': bearish_info if bearish_breakout else None
        }
        
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None


def parallel_scan(stocks, period="6mo", interval="1h", timeframe="4H", 
                 detection_length=20, lookback_bars=5, min_breakout_pct=0.5, 
                 num_processes=None):
    """
    Scan stocks in parallel
    
    Parameters
    ----------
    stocks : list
        List of stock symbols
    num_processes : int, optional
        Number of parallel processes (default: CPU count)
    
    Returns
    -------
    tuple
        (breakout_results, proximity_data)
    """
    if num_processes is None:
        num_processes = min(cpu_count(), 10)  # Cap at 10 to avoid overwhelming the API
    
    print(f"Scanning {len(stocks)} stocks using {num_processes} parallel processes...")
    
    # Prepare arguments for each stock
    args_list = [
        (symbol, period, interval, timeframe, detection_length, lookback_bars, min_breakout_pct)
        for symbol in stocks
    ]
    
    # Scan in parallel
    with Pool(processes=num_processes) as pool:
        results = pool.map(scan_single_stock, args_list)
    
    # Filter out None results
    results = [r for r in results if r is not None]
    
    # Separate breakouts and proximity data
    bullish_breakouts = [r for r in results if r['bullish_breakout']]
    bearish_breakouts = [r for r in results if r['bearish_breakout']]
    
    # Calculate proximity data
    proximity_data = []
    for r in results:
        support_distance = abs(r['current_price'] - r['support']) / r['current_price'] * 100 if r['support'] else 999
        resistance_distance = abs(r['current_price'] - r['resistance']) / r['current_price'] * 100 if r['resistance'] else 999
        
        # Determine bias based on proximity to zones or recent breakouts
        # Bullish: within 1% of support OR bullish breakout in last 10 bars OR no resistance (clear path up)
        # Bearish: within 1% of resistance OR bearish breakout in last 10 bars OR no support (clear path down)
        # Neutral: otherwise
        
        # Check for recent breakouts (within last 10 bars)
        recent_bullish_breakout = r['bullish_breakout'] and r['bullish_info']['bars_ago'] <= 10
        recent_bearish_breakout = r['bearish_breakout'] and r['bearish_info']['bars_ago'] <= 10
        
        # Check for no resistance/support
        no_resistance = r['resistance'] is None
        no_support = r['support'] is None
        
        if support_distance <= 1.0 or recent_bullish_breakout or no_resistance:
            bias = 'Bullish'
            nearest_distance = support_distance
        elif resistance_distance <= 1.0 or recent_bearish_breakout or no_support:
            bias = 'Bearish'
            nearest_distance = resistance_distance
        else:
            bias = 'Neutral'
            nearest_distance = min(support_distance, resistance_distance)
        
        proximity_data.append({
            'symbol': r['symbol'],
            'current_price': r['current_price'],
            'support': r['support'],
            'resistance': r['resistance'],
            'support_distance': support_distance,
            'resistance_distance': resistance_distance,
            'bias': bias,
            'nearest_distance': nearest_distance
        })
    
    # Sort by nearest distance
    proximity_data.sort(key=lambda x: x['nearest_distance'])
    
    return {
        'bullish_breakouts': bullish_breakouts,
        'bearish_breakouts': bearish_breakouts,
        'proximity_data': proximity_data
    }


def generate_proximity_report(results, output_file='proximity_report.html'):
    """Generate HTML report from scan results"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    bullish_breakouts = results['bullish_breakouts']
    bearish_breakouts = results['bearish_breakouts']
    proximity_data = results['proximity_data']
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>S&P 500 Proximity Scanner - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .timestamp {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        .number {{
            font-size: 3em;
            font-weight: 700;
            margin: 10px 0;
        }}
        .bullish {{ color: #28a745; }}
        .bearish {{ color: #dc3545; }}
        .section {{
            padding: 30px;
        }}
        .section-title {{
            font-size: 1.8em;
            font-weight: 700;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        tbody tr:hover {{
            background: #f8f9fa;
        }}
        .positive {{ color: #28a745; font-weight: 600; }}
        .negative {{ color: #dc3545; font-weight: 600; }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-style: italic;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
        }}
        .bias-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .bias-bullish {{
            background: #d4edda;
            color: #155724;
        }}
        .bias-bearish {{
            background: #f8d7da;
            color: #721c24;
        }}
        .bias-neutral {{
            background: #e2e3e5;
            color: #383d41;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Watchlist Proximity Scanner</h1>
            <div class="timestamp">4H Timeframe | {timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Breakouts Up</h3>
                <div class="number bullish">{len(bullish_breakouts)}</div>
            </div>
            <div class="summary-card">
                <h3>Breakouts Down</h3>
                <div class="number bearish">{len(bearish_breakouts)}</div>
            </div>
            <div class="summary-card">
                <h3>Total Scanned</h3>
                <div class="number" style="color: #667eea;">{len(proximity_data)}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🚀 Breakouts</div>
"""
    
    # Bullish Breakouts
    if bullish_breakouts:
        html += """
            <h3 style="color: #28a745; margin-top: 20px;">Bullish Breakouts</h3>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Broke Level</th>
                        <th>Breakout %</th>
                        <th>Bars Ago</th>
                    </tr>
                </thead>
                <tbody>
"""
        for r in sorted(bullish_breakouts, key=lambda x: x['bullish_info']['breakout_pct'], reverse=True):
            info = r['bullish_info']
            html += f"""
                    <tr>
                        <td><strong>{r['symbol']}</strong></td>
                        <td>${r['current_price']:.2f}</td>
                        <td>${info['zone_level']:.2f}</td>
                        <td class="positive">+{info['breakout_pct']:.2f}%</td>
                        <td>{info['bars_ago']}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<p class="no-data">No bullish breakouts found</p>'
    
    # Bearish Breakouts
    if bearish_breakouts:
        html += """
            <h3 style="color: #dc3545; margin-top: 20px;">Bearish Breakouts</h3>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Broke Level</th>
                        <th>Breakout %</th>
                        <th>Bars Ago</th>
                    </tr>
                </thead>
                <tbody>
"""
        for r in sorted(bearish_breakouts, key=lambda x: x['bearish_info']['breakout_pct'], reverse=True):
            info = r['bearish_info']
            html += f"""
                    <tr>
                        <td><strong>{r['symbol']}</strong></td>
                        <td>${r['current_price']:.2f}</td>
                        <td>${info['zone_level']:.2f}</td>
                        <td class="negative">-{info['breakout_pct']:.2f}%</td>
                        <td>{info['bars_ago']}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<p class="no-data">No bearish breakouts found</p>'
    
    # Proximity Table
    html += """
        </div>
        
        <div class="section">
            <div class="section-title">🎯 Proximity to Support/Resistance</div>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Support</th>
                        <th>Resistance</th>
                        <th>Dist to Support</th>
                        <th>Dist to Resistance</th>
                        <th>Bias</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for stock in proximity_data[:100]:  # Show top 100 for readability
        bias_class = 'bias-bullish' if stock['bias'] == 'Bullish' else 'bias-bearish' if stock['bias'] == 'Bearish' else 'bias-neutral'
        support_str = f"${stock['support']:.2f}" if stock['support'] else "N/A"
        resistance_str = f"${stock['resistance']:.2f}" if stock['resistance'] else "N/A"
        support_dist_str = f"{stock['support_distance']:.2f}%" if stock['support_distance'] < 999 else "N/A"
        resistance_dist_str = f"{stock['resistance_distance']:.2f}%" if stock['resistance_distance'] < 999 else "N/A"
        
        html += f"""
                <tr>
                    <td><strong>{stock['symbol']}</strong></td>
                    <td>${stock['current_price']:.2f}</td>
                    <td>{support_str}</td>
                    <td>{resistance_str}</td>
                    <td>{support_dist_str}</td>
                    <td>{resistance_dist_str}</td>
                    <td><span class="bias-badge {bias_class}">{stock['bias']}</span></td>
                </tr>
"""
    
    html += f"""
                </tbody>
            </table>
            <p style="text-align: center; color: #6c757d; margin-top: 20px;">
                Showing top 100 stocks by proximity. Total scanned: {len(proximity_data)}
            </p>
        </div>
        
        <div class="footer">
            <p><strong>Parallel Scan</strong> | <strong>4H Timeframe</strong> | <strong>ATR-based zones</strong> | <strong>Stale zones filtered</strong></p>
            <p>Scanned {len(proximity_data)} S&P 500 stocks</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    import time
    start_time = time.time()
    
    print(f"\n🚀 Parallel S&P 500 Scanner - {len(WATCHLIST)} stocks\n")
    
    # Run parallel scan with 4H timeframe
    results = parallel_scan(
        WATCHLIST,
        period="6mo",        # 6 months of data
        interval="1h",       # 1-hour bars
        timeframe="4H",      # 4-hour timeframe
        detection_length=20,
        lookback_bars=5,
        min_breakout_pct=0.5,
        num_processes=10  # Adjust based on your CPU
    )
    
    # Generate report
    print("\n📊 Generating report...")
    report_file = generate_proximity_report(results)
    
    elapsed = time.time() - start_time
    print(f"\n🎉 Done in {elapsed:.1f} seconds!")
    print(f"   - Bullish breakouts: {len(results['bullish_breakouts'])}")
    print(f"   - Bearish breakouts: {len(results['bearish_breakouts'])}")
    print(f"   - Total stocks scanned: {len(results['proximity_data'])}")
    print(f"\nOpen {report_file} in your browser.\n")
