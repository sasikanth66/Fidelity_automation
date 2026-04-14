"""
Combined Scanner - Shows both bounces and breakouts with proper filtering
Only reports signals that actually happened within the lookback period
"""

from datetime import datetime
from stock_scanner import SupportResistanceScanner
from breakout_scanner import BreakoutScanner
from large_cap_stocks import LARGE_CAP_STOCKS

def generate_combined_report(bounce_scanner, breakout_scanner, output_file='combined_report.html'):
    """Generate HTML report combining both scanners"""
    
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
    <title>Stock Scanner Report - {timestamp}</title>
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
            <h1>📊 Complete Stock Scanner</h1>
            <div class="timestamp">Large Cap Stocks (>$10B) | {timestamp}</div>
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
            <div class="section-title">🚀 Breakouts (Verified Recent)</div>
            <div class="note">
                <strong>Note:</strong> Breakouts are verified to have occurred within the last 5 bars and price is staying above/below the broken level.
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
            <div class="section-title">🎯 Bounces (Support & Resistance)</div>
            <div class="note">
                <strong>Note:</strong> Bounces show stocks that touched nearby support/resistance zones within the lookback period.
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
            <p><strong>Breakouts:</strong> Price broke through level within last 5 bars and is staying above/below it</p>
            <p><strong>Bounces:</strong> Price touched level and bounced back (may include older signals)</p>
            <p>4H Timeframe | Lookback: 5 bars | Only zones within 20% of current price</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Combined report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    print(f"\n🔍 Running Combined Scanner - {len(LARGE_CAP_STOCKS)} Large Cap Stocks (>$10B)\n")
    
    # Run breakout scanner (most reliable)
    print("Running breakout scanner...")
    breakout_scanner = BreakoutScanner(
        stocks=LARGE_CAP_STOCKS,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5,
        min_breakout_pct=0.5
    )
    breakout_scanner.scan_all(max_stocks=None, delay=0.3)
    
    # Run bounce scanner (for reference)
    print("\nRunning bounce scanner...")
    bounce_scanner = SupportResistanceScanner(
        stocks=LARGE_CAP_STOCKS,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5
    )
    bounce_scanner.scan_all(max_stocks=None, delay=0.3)
    
    # Generate combined report
    print("\n📊 Generating combined report...")
    report_file = generate_combined_report(bounce_scanner, breakout_scanner)
    
    print(f"\n🎉 Done! Open {report_file} in your browser.\n")
    print("💡 Recommendation: Focus on the BREAKOUT signals - they are verified and more reliable.")
