"""
live_nav_fetch.py - Mutual Funds Live NAV Ingestion Engine

Fetches live and historical Net Asset Value (NAV) data directly from the official mfapi.in API endpoints:
- HDFC Top 100 Direct Plan (Scheme Code: 125497)
- SBI Bluechip Direct Plan (Scheme Code: 119551)
- ICICI Prudential Bluechip Direct Plan (Scheme Code: 120503)
- Nippon India Large Cap Direct Plan (Scheme Code: 118632)
- Axis Bluechip Direct Plan (Scheme Code: 119092)
- Kotak Bluechip Direct Plan (Scheme Code: 120841)

Parses JSON responses, validates schema, and exports raw and consolidated CSV datasets to data/raw/.
"""

import os
import sys
import json
import logging
import requests
import pandas as pd
from datetime import datetime

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("LiveNAVFetcher")

# Base API Endpoint
BASE_API_URL = "https://api.mfapi.in/mf"

# Key AMFI Schemes Specification
TARGET_SCHEMES = {
    125497: {"name": "HDFC Top 100 Fund - Direct Plan - Growth", "slug": "hdfc_top100"},
    119551: {"name": "SBI Bluechip Fund - Direct Plan - Growth", "slug": "sbi_bluechip"},
    120503: {"name": "ICICI Prudential Bluechip Fund - Direct Plan - Growth", "slug": "icici_bluechip"},
    118632: {"name": "Nippon India Large Cap Fund - Direct Plan - Growth", "slug": "nippon_largecap"},
    119092: {"name": "Axis Bluechip Fund - Direct Plan - Growth", "slug": "axis_bluechip"},
    120841: {"name": "Kotak Bluechip Fund - Direct Plan - Growth", "slug": "kotak_bluechip"},
}

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")


def ensure_directories():
    """Ensure data/raw directory exists."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    logger.info(f"Target raw directory verified: {RAW_DATA_DIR}")


def fetch_scheme_nav(scheme_code: int) -> dict:
    """
    Fetch raw JSON response for a given AMFI scheme code from mfapi.in API.
    """
    url = f"{BASE_API_URL}/{scheme_code}"
    logger.info(f"Executing GET request: {url}")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        if "data" not in data or "meta" not in data:
            raise ValueError(f"Invalid API response format for scheme code {scheme_code}")
        return data
    except Exception as e:
        logger.error(f"Failed to fetch scheme {scheme_code}: {str(e)}")
        raise


def parse_and_save_scheme(scheme_code: int, meta_info: dict, raw_json: dict) -> pd.DataFrame:
    """
    Parse scheme JSON data and write individual CSV artifact.
    """
    meta = raw_json.get("meta", {})
    nav_data = raw_json.get("data", [])

    df = pd.DataFrame(nav_data)
    required_cols = {"date", "nav"}

    if not required_cols.issubset(df.columns):
        raise ValueError("Unexpected API schema")
    if df.empty:
        logger.warning(f"No NAV records returned for scheme code {scheme_code}")
        return pd.DataFrame()

    # Parse and clean NAV columns
    df["scheme_code"] = int(scheme_code)
    df["scheme_name"] = meta.get("scheme_name", meta_info["name"])
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
    
    # Sort chronologically
    df = df.sort_values("date").reset_index(drop=True)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Format output file path
    slug = meta_info["slug"]
    output_filename = f"{slug}_{scheme_code}_live.csv"
    output_path = os.path.join(RAW_DATA_DIR, output_filename)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} NAV records for [{meta_info['name']}] to {output_path}")

    # Also save raw mfapi json format if 125497 (HDFC Top 100)
    if scheme_code == 125497:
        hdfc_raw_path = os.path.join(RAW_DATA_DIR, "live_nav_hdfc_top100.csv")
        df.to_csv(hdfc_raw_path, index=False)
        logger.info(f"Created dedicated HDFC Top 100 raw artifact at {hdfc_raw_path}")

    return df


def main():
    logger.info("Starting Live NAV Fetching Process from mfapi.in")
    ensure_directories()

    all_nav_frames = []

    for scheme_code, meta_info in TARGET_SCHEMES.items():
        try:
            raw_json = fetch_scheme_nav(scheme_code)
            df = parse_and_save_scheme(scheme_code, meta_info, raw_json)
            if not df.empty:
                all_nav_frames.append(df)
        except Exception as e:
            logger.error(f"Skipping scheme {scheme_code} due to error: {e}")

    if all_nav_frames:
        consolidated_df = pd.concat(all_nav_frames, ignore_index=True)
        consolidated_path = os.path.join(RAW_DATA_DIR, "live_nav_consolidated_key_schemes.csv")
        consolidated_df.to_csv(consolidated_path, index=False)
        logger.info(f"Successfully consolidated {len(consolidated_df)} NAV records into {consolidated_path}")

    logger.info("Live NAV Ingestion Completed Successfully.")


if __name__ == "__main__":
    main()
