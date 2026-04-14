"""
Custom Watchlist Scanner - 1H Timeframe
Scans your specific watchlist with 1-hour candles
"""

from datetime import datetime
from stock_scanner import SupportResistanceScanner
from breakout_scanner import BreakoutScanner

# Your custom watchlist
WATCHLIST = [
    'AAPL', 'NVDA', 'MSFT', 'RKLB', 'ASTS', 'AVGO', 'TSLA', 'MU', 'SNDK', 'META',
    'AMZN', 'HOOD', 'APLD', 'TSM', 'SPY', 'QQQ', 'SMH', 'QCOM', 'LLY', 'MSTR',
    'COIN', 'TGT', 'ANF', 'CRM', 'SOUN', 'LULU', 'PLTR', 'ASML', 'AMD', 'GOOG'
]

def generate_watchlist_report(bounce_scanner, breakout_scanner, output_file='watchlist_report.html'):
    """Generate HTML report for watchlist"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Count signals
    support_bounces = len(bounce_scanner.results['support_bounces'])
    resistance_bounces = len(bounce_scanner.results['resistance_bounces'])
    bullish_breakouts = len(breakout_scanner.results['bullish_breakouts'])
    bearish_breakouts = len(breakout_scanner.results['bearish_breakouts'])
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Watchlist Scanner - {timestamp}</title>
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
        .strength {{ font-size: 1.2em; }}
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Watchlist Scanner</h1>
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
                <h3>Support Bounces</h3>
                <div class="number bullish">{support_bounces}</div>
            </div>
            <div class="summary-card">
                <h3>Resistance Bounces</h3>
                <div class="number bearish">{resistance_bounces}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🚀 Breakouts</div>
            <div class="note">
                <strong>Note:</strong> Breakouts are verified - price crossed the level within last 5 bars and is staying above/below it.
            </div>
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
                        <th>Strength</th>
                    </tr>
                </thead>
                <tbody>
"""
        for result in sorted(breakout_scanner.results['bullish_breakouts'],
                           key=lambda x: x['bullish_info']['breakout_pct'], reverse=True):
            info = result['bullish_info']
            strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"
            
            html += f"""
                    <tr>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>${result['current_price']:.2f}</td>
                        <td>${info['zone_level']:.2f}</td>
                        <td class="positive">+{info['breakout_pct']:.2f}%</td>
                        <td>{info['bars_ago']}</td>
                        <td class="strength">{strength}</td>
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
                        <th>Strength</th>
                    </tr>
                </thead>
                <tbody>
"""
        for result in sorted(breakout_scanner.results['bearish_breakouts'],
                           key=lambda x: x['bearish_info']['breakout_pct'], reverse=True):
            info = result['bearish_info']
            strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"
            
            html += f"""
                    <tr>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>${result['current_price']:.2f}</td>
                        <td>${info['zone_level']:.2f}</td>
                        <td class="negative">-{info['breakout_pct']:.2f}%</td>
                        <td>{info['bars_ago']}</td>
                        <td class="strength">{strength}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<p class="no-data">No bearish breakouts found</p>'
    
    html += """
        </div>
        
        <div class="section">
            <div class="section-title">🎯 Bounces</div>
            <div class="note">
                <strong>Note:</strong> Bounces show stocks that touched nearby support/resistance zones.
            </div>
"""
    
    # Support Bounces
    if support_bounces > 0:
        html += """
            <h3 style="color: #28a745; margin-top: 20px;">Support Bounces (Bullish)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Support Level</th>
                        <th>Distance</th>
                        <th>Bars Ago</th>
                        <th>Strength</th>
                    </tr>
                </thead>
                <tbody>
"""
        for result in sorted(bounce_scanner.results['support_bounces'],
                           key=lambda x: abs(x['support_info']['distance_pct'])):
            info = result['support_info']
            strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"
            
            html += f"""
                    <tr>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>${result['current_price']:.2f}</td>
                        <td>${info['zone_level']:.2f}</td>
                        <td class="positive">+{info['distance_pct']:.2f}%</td>
                        <td>{info['bars_ago']}</td>
                        <td class="strength">{strength}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<p class="no-data">No support bounces found</p>'
    
    # Resistance Bounces
    if resistance_bounces > 0:
        html += """
            <h3 style="color: #dc3545; margin-top: 20px;">Resistance Bounces (Bearish)</h3>
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Resistance Level</th>
                        <th>Distance</th>
                        <th>Bars Ago</th>
                        <th>Strength</th>
                    </tr>
                </thead>
                <tbody>
"""
        for result in sorted(bounce_scanner.results['resistance_bounces'],
                           key=lambda x: abs(x['resistance_info']['distance_pct'])):
            info = result['resistance_info']
            strength = "🔥🔥🔥" if info['bars_ago'] == 0 else "🔥🔥" if info['bars_ago'] == 1 else "🔥"
            
            html += f"""
                    <tr>
                        <td><strong>{result['symbol']}</strong></td>
                        <td>${result['current_price']:.2f}</td>
                        <td>${info['zone_level']:.2f}</td>
                        <td class="negative">-{info['distance_pct']:.2f}%</td>
                        <td>{info['bars_ago']}</td>
                        <td class="strength">{strength}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<p class="no-data">No resistance bounces found</p>'
    
    html += """
        </div>
        
        <div class="footer">
            <p><strong>Timeframe:</strong> 4H candles | <strong>Lookback:</strong> 5 bars | <strong>Zone Filter:</strong> Within 20% of current price</p>
            <p>Breakouts = Verified transitions | Bounces = Touches of S/R zones with ATR-based sizing</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Watchlist report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    print(f"\n🔍 Scanning Watchlist ({len(WATCHLIST)} stocks) - 4H Timeframe\n")
    
    # Run breakout scanner
    print("Running breakout scanner...")
    breakout_scanner = BreakoutScanner(
        stocks=WATCHLIST,
        period="6mo",
        interval="1h",
        timeframe="4H",  # 4-hour candles
        detection_length=20,
        lookback_bars=5,
        min_breakout_pct=0.5
    )
    breakout_scanner.scan_all(max_stocks=None, delay=0.3)
    
    # Run bounce scanner
    print("\nRunning bounce scanner...")
    bounce_scanner = SupportResistanceScanner(
        stocks=WATCHLIST,
        period="6mo",
        interval="1h",
        timeframe="4H",  # 4-hour candles
        detection_length=20,
        lookback_bars=5
    )
    bounce_scanner.scan_all(max_stocks=None, delay=0.3)
    
    # Generate report
    print("\n📊 Generating watchlist report...")
    report_file = generate_watchlist_report(bounce_scanner, breakout_scanner)
    
    print(f"\n🎉 Done! Open {report_file} in your browser.\n")
