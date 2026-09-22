import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
with open('ticker_index.json', 'r', encoding='utf-8') as f:
    ti = json.load(f).get('tickers', {})

test_tickers = ['PC1', 'TKV', 'VIB', 'VIC', 'VFS', 'SSI', 'VHM', 'ALC', 'STB', 'LPB', 'MSR', 'C21', 'HVN', 'CTG', 'BTD', 'BID', 'HBC', 'SBT', 'APG', 'NDC', 'DTR', 'TPB', 'DQC', 'EVN']
for t in test_tickers:
    if t in ti:
        print(f"{t}: {ti[t].get('company_en')} | {ti[t].get('exchange')} | {ti[t].get('sector_key')}")
    else:
        print(f"{t}: NOT FOUND")
