"""Load the repository CSV into SQLite, validate, execute SQL and export results.

Run from any directory: python SQL/load_market_data.py
Uses only the Python standard library; SQLite >= 3.25 is required.
"""
import argparse
import csv
from datetime import datetime, timedelta
import math
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {
    'purchase_bid_(mw)': 'purchase_bid_mw',
    'sell_bid_(mw)': 'sell_bid_mw',
    'mcv_(mw)': 'mcv_mw',
    'final_scheduled_volume_(mw)': 'final_scheduled_volume_mw',
    'mcp_(rs/mwh)_*': 'mcp_rs_mwh',
}

def load_rows(path):
    with path.open(newline='', encoding='utf-8-sig') as source:
        reader = csv.DictReader(source)
        required = {'date', 'timestamp', 'time_block'} | FIELDS.keys()
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing CSV columns: {sorted(missing)}')
        rows = []
        for line, raw in enumerate(reader, 2):
            try:
                stamp = datetime.strptime(raw['timestamp'], '%Y-%m-%d %H:%M:%S')
                day = datetime.strptime(raw['date'], '%d-%m-%Y').date()
                if stamp.date() != day or stamp.minute % 15 or stamp.second:
                    raise ValueError('timestamp/date mismatch or off-grid timestamp')
                values = [float(raw[name]) for name in FIELDS]
                if not all(math.isfinite(v) for v in values):
                    raise ValueError('non-finite numeric input')
                if any(v < 0 for v in values[:4]):
                    raise ValueError('negative power quantity')
                rows.append((day.isoformat(), stamp.isoformat(sep=' '), raw['time_block'], *values))
            except (ValueError, KeyError) as error:
                raise ValueError(f'CSV line {line}: {error}') from error
    if not rows:
        raise ValueError('CSV contains no observations')
    # Validate full days before replacing an existing database.
    days = {}
    for row in rows:
        days.setdefault(row[0], []).append(row[1])
    for day, stamps in days.items():
        start = datetime.fromisoformat(day)
        expected = {(start + timedelta(minutes=15*i)).isoformat(sep=' ') for i in range(96)}
        if len(stamps) != 96 or set(stamps) != expected:
            raise ValueError(f'{day}: expected exactly 96 unique intervals from 00:00 to 23:45')
    return rows

def export_query(connection, query, destination):
    result = connection.execute(query)
    with destination.open('w', newline='', encoding='utf-8') as output:
        writer = csv.writer(output)
        writer.writerow([col[0] for col in result.description])
        writer.writerows(result)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--csv', type=Path, default=ROOT / 'Exports/cleaned_dam_data.csv')
    parser.add_argument('--database', type=Path, default=ROOT / 'SQL/market_data.sqlite')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'Exports')
    args = parser.parse_args()
    rows = load_rows(args.csv)
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(args.database) as db:
        db.execute('DROP TABLE IF EXISTS dam_intervals')
        db.execute('''CREATE TABLE dam_intervals (
            market_date TEXT NOT NULL, timestamp TEXT PRIMARY KEY,
            time_block TEXT NOT NULL,
            purchase_bid_mw REAL NOT NULL CHECK(purchase_bid_mw >= 0),
            sell_bid_mw REAL NOT NULL CHECK(sell_bid_mw >= 0),
            mcv_mw REAL NOT NULL CHECK(mcv_mw >= 0),
            final_scheduled_volume_mw REAL NOT NULL CHECK(final_scheduled_volume_mw >= 0),
            mcp_rs_mwh REAL NOT NULL)''')
        db.executemany('INSERT INTO dam_intervals VALUES (?,?,?,?,?,?,?,?)', rows)
        db.executescript((ROOT / 'SQL/market_analysis.sql').read_text())
        for view, order in [
            ('data_quality', 'market_date'), ('daily_summary', 'market_date'),
            ('hourly_profile', 'market_date, clock_hour'), ('interval_metrics', 'timestamp'),
            ('price_movement_ranking', 'market_date, movement_rank, timestamp'),
            ('fulfilment_ranking', 'market_date, lowest_fulfilment_rank, timestamp'),
            ('maximum_price_runs', 'market_date, start_inclusive')]:
            export_query(db, f'SELECT * FROM {view} ORDER BY {order}',
                         args.output_dir / f'sql_{view}.csv')
        print(f'Loaded {len(rows)} validated intervals from {args.csv.name}')
        print('Daily summary:', db.execute('SELECT * FROM daily_summary').fetchall())
        print('Maximum-price runs:', db.execute('SELECT * FROM maximum_price_runs').fetchall())
        print(f'Exported seven query results to {args.output_dir}')

if __name__ == '__main__':
    main()
