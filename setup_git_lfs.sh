#!/bin/bash
set -e

echo "🚀 SETTING UP GIT LFS FOR MARKET DATA"
echo "====================================="
echo ""

REPO="/tmp/event-driven-platform"
DATA_DIR="$REPO/data/market_data"
COMPRESSED_DIR="$REPO/data/compressed"

# Step 1: Initialize Git LFS
echo "Step 1: Initializing Git LFS..."
cd "$REPO"
git lfs install --local
echo "✅ Git LFS initialized"
echo ""

# Step 2: Create .gitattributes for LFS tracking
echo "Step 2: Configuring LFS file patterns..."
cat > .gitattributes << 'GITATTRIBEOF'
# Large compressed data files
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.tar.bz2 filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text
*.parquet filter=lfs diff=lfs merge=lfs -text
*.db filter=lfs diff=lfs merge=lfs -text
*.sqlite3 filter=lfs diff=lfs merge=lfs -text

# Large CSV files (uncompressed - for reference only)
data/market_data/*.csv filter=lfs diff=lfs merge=lfs -text

# Checksum files
*.sha256 filter=lfs diff=lfs merge=lfs -text
GITATTRIBEOF

git add .gitattributes
echo "✅ .gitattributes configured"
echo ""

# Step 3: Create data directories
echo "Step 3: Creating data directories..."
mkdir -p "$DATA_DIR" "$COMPRESSED_DIR"
mkdir -p "$REPO/data/schemas"
echo "✅ Directories created"
echo ""

# Step 4: Generate sample market data
echo "Step 4: Generating sample 8-market OHLCV data..."
python3 << 'PYSCRIPT'
import json
import gzip
import pandas as pd
from datetime import datetime, timedelta
import random
import os

def generate_market_data(market, num_stocks, num_days=1250):
    """Generate 5 years of OHLCV data (1250 trading days)"""
    data = []
    base_date = datetime.now() - timedelta(days=1250)
    
    for stock_idx in range(num_stocks):
        ticker = f"{market.upper()}_STOCK_{stock_idx:04d}"
        price = random.uniform(100, 10000)
        
        for day in range(num_days):
            current_date = base_date + timedelta(days=day)
            if current_date.weekday() >= 5:  # Skip weekends
                continue
            
            open_price = price * random.uniform(0.99, 1.01)
            high_price = max(open_price, price) * random.uniform(1.0, 1.02)
            low_price = min(open_price, price) * random.uniform(0.98, 1.0)
            close_price = random.uniform(low_price, high_price)
            volume = random.randint(100000, 10000000)
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'market': market,
                'ticker': ticker,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume,
            })
            
            price = close_price
    
    return pd.DataFrame(data)

# Markets and stock counts
markets_config = {
    'india': 500,    # NSE/BSE
    'usa': 500,      # NYSE/NASDAQ
    'europe': 300,   # 17 exchanges
    'japan': 300,    # TSE
    'korea': 200,    # KRX
    'uk': 150,       # LSE
    'brazil': 100,   # IBOV
    'china': 150,    # A-shares
}

print("Generating market data for 8 markets...")
print("-" * 60)

all_data = []
total_records = 0

for market, num_stocks in markets_config.items():
    print(f"  {market.upper():8} ({num_stocks} stocks)...", end=' ', flush=True)
    df = generate_market_data(market, num_stocks, num_days=250)  # 1 year for faster demo
    all_data.append(df)
    total_records += len(df)
    print(f"✓ {len(df):,} records")

# Combine all markets
combined_df = pd.concat(all_data, ignore_index=True)
print("-" * 60)
print(f"Total records generated: {total_records:,}")
print(f"Unique markets: {combined_df['market'].nunique()}")
print(f"Unique tickers: {combined_df['ticker'].nunique()}")
print(f"Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")

# Save as compressed CSV
csv_path = '/tmp/event-driven-platform/data/market_data/ohlcv_combined.csv'
combined_df.to_csv(csv_path, index=False)
print(f"\nSaved uncompressed: {csv_path}")
print(f"Size: {os.path.getsize(csv_path) / (1024*1024):.2f} MB")

# Compress with gzip
gz_path = csv_path + '.gz'
with open(csv_path, 'rb') as f_in:
    with gzip.open(gz_path, 'wb') as f_out:
        f_out.writelines(f_in)

orig_size = os.path.getsize(csv_path) / (1024*1024)
comp_size = os.path.getsize(gz_path) / (1024*1024)
ratio = (1 - comp_size/orig_size) * 100

print(f"Saved compressed:    {gz_path}")
print(f"Size: {comp_size:.2f} MB (saved {ratio:.1f}%)")

# Save per-market compressed files
print("\nCompressing per-market data...")
for market in markets_config.keys():
    market_df = combined_df[combined_df['market'] == market].copy()
    market_csv = f'/tmp/event-driven-platform/data/market_data/{market}_ohlcv.csv'
    market_gz = market_csv + '.gz'
    
    market_df.to_csv(market_csv, index=False)
    
    with open(market_csv, 'rb') as f_in:
        with gzip.open(market_gz, 'wb') as f_out:
            f_out.writelines(f_in)
    
    size = os.path.getsize(market_gz) / (1024*1024)
    print(f"  {market.upper():8} → {market_gz} ({size:.2f} MB)")
    os.remove(market_csv)  # Remove uncompressed

# Generate schema file
schema = {
    'version': '1.0',
    'created': datetime.now().isoformat(),
    'markets': list(markets_config.keys()),
    'total_stocks': sum(markets_config.values()),
    'total_records': int(total_records),
    'columns': ['date', 'market', 'ticker', 'open', 'high', 'low', 'close', 'volume'],
    'date_range': {
        'start': combined_df['date'].min(),
        'end': combined_df['date'].max(),
    },
}

schema_path = '/tmp/event-driven-platform/data/market_data/SCHEMA.json'
with open(schema_path, 'w') as f:
    json.dump(schema, f, indent=2)

print(f"\nSchema file: {schema_path}")
print(json.dumps(schema, indent=2))

PYSCRIPT

echo ""
echo "Step 5: Creating checksums..."
cd "$REPO/data/market_data"
ls -1 *.gz 2>/dev/null | xargs -I {} sh -c 'shasum -a 256 {} > {}.sha256'
echo "✅ Checksums created"
echo ""

echo "Step 6: Adding files to Git LFS..."
cd "$REPO"
git add -A
git status --porcelain | head -20
echo ""

echo "Step 7: Summary"
echo "=============="
echo ""
ls -lh data/market_data/ 2>/dev/null || echo "No data directory yet"
du -sh data/ 2>/dev/null || echo "Data directory size pending"
echo ""

# Show LFS status
echo "Git LFS Status:"
git lfs ls-files | head -10
echo ""

