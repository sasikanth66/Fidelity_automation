"""
Proximity Scanner - Shows breakouts and proximity to support/resistance
Stocks are classified as bullish (near support) or bearish (near resistance)
"""

from datetime import datetime
from stock_scanner import SupportResistanceScanner
from breakout_scanner import BreakoutScanner
from sp500_stocks import SP500_STOCKS

# Use S&P 500 stocks
WATCHLIST = SP500_STOCKS

def generate_proximity_report(scanner, breakout_scanner, output_file='proximity_report.html'):
    """Generate HTML report showing breakouts and proximity to S/R levels"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Collect all stocks with their proximity data
    proximity_data = []
    
    # Get all scanned stocks from the scanner
    for result in scanner.results['support_bounces'] + scanner.results['resistance_bounces']:
        symbol = result['symbol']
        current_price = result['current_price']
        
        # Find nearest support and resistance
        support_level = result.get('support_info', {}).get('zone_level') if result.get('support_info') else None
        resistance_level = result.get('resistance_info', {}).get('zone_level') if result.get('resistance_info') else None
        
        # Calculate distances
        support_distance = abs(current_price - support_level) / current_price * 100 if support_level else 999
        resistance_distance = abs(current_price - resistance_level) / current_price * 100 if resistance_level else 999
        
        # Determine bias
        if support_distance < resistance_distance:
            bias = 'Bullish'
            nearest_distance = support_distance
        else:
            bias = 'Bearish'
            nearest_distance = resistance_distance
        
        proximity_data.append({
            'symbol': symbol,
            'current_price': current_price,
            'support': support_level,
            'resistance': resistance_level,
            'support_distance': support_distance,
            'resistance_distance': resistance_distance,
            'bias': bias,
            'nearest_distance': nearest_distance
        })
    
    # Sort by nearest distance (closest to S/R first)
    proximity_data.sort(key=lambda x: x['nearest_distance'])
    
    # Count breakouts
    bullish_breakouts = len(breakout_scanner.results['bullish_breakouts'])
    bearish_breakouts = len(breakout_scanner.results['bearish_breakouts'])
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Proximity Scanner - {timestamp}</title>
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
        .note {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Proximity Scanner</h1>
            <div class="timestamp">4H Timeframe | {timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Breakouts Up</h3>
                <div class="number bullish">{bullish_breakouts}</div>
            </div>
            <div class="summary-card">
                <h3>Breakouts Down</h3>
                <div class="number bearish">{bearish_breakouts}</div>
            </div>
            <div class="summary-card">
                <h3>Total Stocks</h3>
                <div class="number" style="color: #667eea;">{len(proximity_data)}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🚀 Breakouts</div>
"""
    
    # Bullish Breakouts
    if bullish_breakouts > 0:
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
        for result in sorted(breakout_scanner.results['bullish_breakouts'],
                           key=lambda x: x['bullish_info']['breakout_pct'], reverse=True):
            info = result['bullish_info']
            
            html += f"""
                    <tr>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>${result['current_price']:.2f}</td>
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
    if bearish_breakouts > 0:
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
        for result in sorted(breakout_scanner.results['bearish_breakouts'],
                           key=lambda x: x['bearish_info']['breakout_pct'], reverse=True):
            info = result['bearish_info']
            
            html += f"""
                    <tr>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>${result['current_price']:.2f}</td>
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
            <div class="note">
                <strong>Note:</strong> Stocks ordered by proximity to nearest S/R level. Bullish = closer to support, Bearish = closer to resistance.
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Support</th>
                        <th>Resistance</th>
                        <th>Distance to Support</th>
                        <th>Distance to Resistance</th>
                        <th>Bias</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for stock in proximity_data:
        bias_class = 'bias-bullish' if stock['bias'] == 'Bullish' else 'bias-bearish'
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
    
    html += """
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p><strong>Timeframe:</strong> 4H candles | <strong>ATR-based zones</strong> | <strong>Stale zones filtered</strong> (>50 bars inactive)</p>
            <p>Breakouts = Verified recent transitions | Proximity = Distance to nearest active S/R level</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Proximity report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    print(f"\n🔍 Running Proximity Scanner ({len(WATCHLIST)} stocks) - 4H Timeframe\n")
    
    # Run breakout scanner
    print("Running breakout scanner...")
    breakout_scanner = BreakoutScanner(
        stocks=WATCHLIST,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5,
        min_breakout_pct=0.5
    )
    breakout_scanner.scan_all(max_stocks=None, delay=0.3)
    
    # Run bounce scanner (to get proximity data)
    print("\nScanning for S/R levels...")
    bounce_scanner = SupportResistanceScanner(
        stocks=WATCHLIST,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5
    )
    bounce_scanner.scan_all(max_stocks=None, delay=0.3)
    
    # Generate report
    print("\n📊 Generating proximity report...")
    report_file = generate_proximity_report(bounce_scanner, breakout_scanner)
    
    print(f"\n🎉 Done! Open {report_file} in your browser.\n")
