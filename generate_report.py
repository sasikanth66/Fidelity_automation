"""
Generate HTML Report for Stock Scanner Results
Runs both bounce and breakout scanners and creates a detailed HTML report
"""

import pandas as pd
from datetime import datetime
from stock_scanner import SupportResistanceScanner
from breakout_scanner import BreakoutScanner
from large_cap_stocks import LARGE_CAP_STOCKS

def generate_html_report(bounce_scanner, breakout_scanner, output_file='scanner_report.html'):
    """Generate a comprehensive HTML report from scanner results"""
    
    # Get current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Start building HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Stock Scanner Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
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
            font-weight: 700;
        }}
        .header .timestamp {{
            margin-top: 10px;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .summary-card .number {{
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
        .subsection-title {{
            font-size: 1.3em;
            font-weight: 600;
            margin: 30px 0 15px 0;
            color: #495057;
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
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
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
        .strength {{
            font-size: 1.2em;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-bullish {{
            background: #d4edda;
            color: #155724;
        }}
        .badge-bearish {{
            background: #f8d7da;
            color: #721c24;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Stock Scanner Report</h1>
            <div class="timestamp">Generated: {timestamp}</div>
        </div>
"""
    
    # Summary statistics
    bounce_support = len(bounce_scanner.results['support_bounces'])
    bounce_resistance = len(bounce_scanner.results['resistance_bounces'])
    breakout_bullish = len(breakout_scanner.results['bullish_breakouts'])
    breakout_bearish = len(breakout_scanner.results['bearish_breakouts'])
    
    html += f"""
        <div class="summary">
            <div class="summary-card">
                <h3>Support Bounces</h3>
                <div class="number bullish">{bounce_support}</div>
                <div class="badge badge-bullish">Bullish</div>
            </div>
            <div class="summary-card">
                <h3>Resistance Bounces</h3>
                <div class="number bearish">{bounce_resistance}</div>
                <div class="badge badge-bearish">Bearish</div>
            </div>
            <div class="summary-card">
                <h3>Bullish Breakouts</h3>
                <div class="number bullish">{breakout_bullish}</div>
                <div class="badge badge-bullish">Breakout Up</div>
            </div>
            <div class="summary-card">
                <h3>Bearish Breakouts</h3>
                <div class="number bearish">{breakout_bearish}</div>
                <div class="badge badge-bearish">Breakout Down</div>
            </div>
        </div>
"""
    
    # Bounce Scanner Results
    html += """
        <div class="section">
            <div class="section-title">🎯 Bounce Scanner Results</div>
"""
    
    # Support Bounces
    html += """
            <div class="subsection-title">🟢 Support Bounces (Bullish Setups)</div>
"""
    
    if bounce_support > 0:
        html += """
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
        html += '<div class="no-data">No support bounces found</div>'
    
    # Resistance Bounces
    html += """
            <div class="subsection-title">🔴 Resistance Bounces (Bearish Setups)</div>
"""
    
    if bounce_resistance > 0:
        html += """
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
        html += '<div class="no-data">No resistance bounces found</div>'
    
    html += """
        </div>
"""
    
    # Breakout Scanner Results
    html += """
        <div class="section">
            <div class="section-title">🚀 Breakout Scanner Results</div>
"""
    
    # Bullish Breakouts
    html += """
            <div class="subsection-title">🟢 Bullish Breakouts (Broke Above Resistance)</div>
"""
    
    if breakout_bullish > 0:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Broke Level</th>
                        <th>Breakout %</th>
                        <th>Distance</th>
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
        html += '<div class="no-data">No bullish breakouts found</div>'
    
    # Bearish Breakouts
    html += """
            <div class="subsection-title">🔴 Bearish Breakouts (Broke Below Support)</div>
"""
    
    if breakout_bearish > 0:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Current Price</th>
                        <th>Broke Level</th>
                        <th>Breakout %</th>
                        <th>Distance</th>
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
        html += '<div class="no-data">No bearish breakouts found</div>'
    
    html += """
        </div>
"""
    
    # Footer
    html += f"""
        <div class="footer">
            <p>Scan Parameters: 4H Timeframe | Detection Length: 20 | Lookback: 5 bars | Period: 6 months</p>
            <p>Report generated by Stock Scanner System</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"\n✅ HTML report generated: {output_file}")
    return output_file


if __name__ == "__main__":
    print("\n🔍 Running Stock Scanners...\n")
    print(f"📊 Scanning {len(LARGE_CAP_STOCKS)} large cap stocks (market cap > $10B)\n")
    
    # Run bounce scanner
    print("Running bounce scanner...")
    bounce_scanner = SupportResistanceScanner(
        stocks=LARGE_CAP_STOCKS,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5
    )
    bounce_scanner.scan_all(max_stocks=None, delay=0.3)  # Scan all stocks with shorter delay
    
    # Run breakout scanner
    print("\nRunning breakout scanner...")
    breakout_scanner = BreakoutScanner(
        stocks=LARGE_CAP_STOCKS,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5,
        min_breakout_pct=0.5
    )
    breakout_scanner.scan_all(max_stocks=None, delay=0.3)  # Scan all stocks with shorter delay
    
    # Generate HTML report
    print("\n📊 Generating HTML report...")
    report_file = generate_html_report(bounce_scanner, breakout_scanner)
    
    print(f"\n🎉 Done! Open {report_file} in your browser to view the report.\n")
