"""
Simple Breakout Scanner - NASDAQ Top 20
Shows only breakout signals (no bounce detection)
"""

from datetime import datetime
from breakout_scanner import BreakoutScanner

# NASDAQ Top 20 by market cap
NASDAQ_TOP_20 = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 
    'META', 'TSLA', 'AVGO', 'COST', 'NFLX',
    'AMD', 'PEP', 'ADBE', 'CSCO', 'TMUS',
    'CMCSA', 'INTC', 'TXN', 'QCOM', 'AMGN'
]

def generate_breakout_report(scanner, output_file='breakout_report.html'):
    """Generate HTML report for breakout scanner only"""
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    bullish = len(scanner.results['bullish_breakouts'])
    bearish = len(scanner.results['bearish_breakouts'])
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Breakout Scanner Report - {timestamp}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
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
        .timestamp {{
            margin-top: 10px;
            opacity: 0.9;
        }}
        .summary {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            margin: 0 0 15px 0;
            color: #495057;
            font-size: 1em;
            text-transform: uppercase;
        }}
        .number {{
            font-size: 3.5em;
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
            text-transform: uppercase;
            font-size: 0.85em;
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Breakout Scanner</h1>
            <div class="timestamp">NASDAQ Top 20 | {timestamp}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Bullish Breakouts</h3>
                <div class="number bullish">{bullish}</div>
                <p>Broke above resistance</p>
            </div>
            <div class="summary-card">
                <h3>Bearish Breakouts</h3>
                <div class="number bearish">{bearish}</div>
                <p>Broke below support</p>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">🟢 Bullish Breakouts</div>
"""
    
    if bullish > 0:
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
        for result in sorted(scanner.results['bullish_breakouts'],
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
    
    html += """
            <div class="section-title">🔴 Bearish Breakouts</div>
"""
    
    if bearish > 0:
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
        for result in sorted(scanner.results['bearish_breakouts'],
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
    
    html += f"""
        </div>
        
        <div class="footer">
            <p>4H Timeframe | Lookback: 5 bars | Min Breakout: 0.5%</p>
            <p>Breakout = Stock broke through level and is STAYING above/below it</p>
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
    print("\n🔍 Breakout Scanner - NASDAQ Top 20\n")
    
    scanner = BreakoutScanner(
        stocks=NASDAQ_TOP_20,
        period="6mo",
        interval="1h",
        timeframe="4H",
        detection_length=20,
        lookback_bars=5,
        min_breakout_pct=0.5
    )
    
    scanner.scan_all(max_stocks=None, delay=0.5)
    scanner.print_results()
    
    report_file = generate_breakout_report(scanner)
    print(f"\n🎉 Done! Open {report_file} in your browser.\n")
