"""
scripts/live_nav_fetch.py - Live NAV Ingestion from mfapi.in
"""
import sys
import requests
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

KEY_SCHEMES = {
    "125497": "hdfc_top_100",
    "119551": "sbi_bluechip",
    "120503": "icici_bluechip",
    "118632": "nippon_large_cap",
    "119092": "axis_bluechip",
    "120841": "kotak_bluechip"
}

def fetch_live_nav(scheme_code):
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            nav_list = data.get("data", [])
            df = pd.DataFrame(nav_list)
            df["amfi_code"] = scheme_code
            df["scheme_name"] = data.get("meta", {}).get("scheme_name", "")
            return df
    except Exception as e:
        print(f"Warning: Timed out fetching scheme {scheme_code}: {e}")
    return pd.DataFrame()

def main():
    for code, prefix in KEY_SCHEMES.items():
        df = fetch_live_nav(code)
        if not df.empty:
            out_file = RAW_DIR / f"{prefix}_{code}_live.csv"
            df.to_csv(out_file, index=False)
            print(f"Saved {len(df)} live NAV records to {out_file}")

if __name__ == "__main__":
    main()
