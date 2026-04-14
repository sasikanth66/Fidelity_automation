"""
Write watchlist output files (JSON + CSV).
Usage: python write_watchlist.py /tmp/watchlist_selections.json
Writes to outputs/trending_watchlist_YYYYMMDD_HHMMSS.json and .csv
"""

import csv
import json
import os
import sys
from datetime import datetime


OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs')

FIELDS = [
    'rank', 'symbol', 'reason', 'catalyst', 'technical_bias',
    'current_price', 'rsi', 'nearest_support', 'nearest_resistance',
    'support_distance_pct', 'resistance_distance_pct',
    'recent_volume_ratio', 'recent_price_change_pct', 'news_headlines',
]


def main():
    if len(sys.argv) < 2:
        print('Usage: python write_watchlist.py <input_json_file>')
        sys.exit(1)

    input_path = sys.argv[1]

    with open(input_path, 'r') as f:
        selections = json.load(f)

    if not isinstance(selections, list):
        print(f'Error: expected a JSON array, got {type(selections).__name__}')
        sys.exit(1)

    os.makedirs(OUTPUTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base_name = f'trending_watchlist_{timestamp}'
    json_path = os.path.join(OUTPUTS_DIR, f'{base_name}.json')
    csv_path = os.path.join(OUTPUTS_DIR, f'{base_name}.csv')

    # Normalise each record to ensure all fields present
    normalised = []
    for i, item in enumerate(selections):
        record = {field: item.get(field) for field in FIELDS}
        if record.get('rank') is None:
            record['rank'] = i + 1
        # Flatten news_headlines list to a string for CSV
        headlines = record.get('news_headlines') or []
        if isinstance(headlines, list):
            record['news_headlines_str'] = ' | '.join(headlines)
        else:
            record['news_headlines_str'] = str(headlines)
        normalised.append(record)
        print(
            f"  [{i+1:2}/{len(selections)}] {record['symbol']:6}  "
            f"price=${record['current_price']}  RSI={record['rsi']}  "
            f"bias={record['technical_bias']}  catalyst: {str(record['catalyst'])[:60]}"
        )

    # Write JSON
    with open(json_path, 'w') as f:
        json.dump(normalised, f, indent=2)

    # Write CSV
    with open(csv_path, 'w', newline='') as f:
        csv_fields = FIELDS[:-1] + ['news_headlines']  # keep original name in CSV
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        for record in normalised:
            row = {field: record.get(field) for field in FIELDS[:-1]}
            row['news_headlines'] = record['news_headlines_str']
            writer.writerow(row)

    print(f'JSON: {json_path}')
    print(f'CSV:  {csv_path}')
    print(f'Written {len(normalised)} stocks to watchlist.')


if __name__ == '__main__':
    main()
