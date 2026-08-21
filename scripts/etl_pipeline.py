"""
scripts/etl_pipeline.py - Standalone Reproducible Master ETL Pipeline

Cleans all raw Bluestock datasets, applies weekend/holiday NAV forward-filling,
validates schema & numeric ranges, loads data into SQLite Star Schema database (data/db/bluestock_mf.db),
and executes row-count parity verification between CSV source files and SQLite DB tables.

Usage:
    python scripts/etl_pipeline.py
"""

import sys
import sqlite3
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Enforce UTF-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"
DB_DIR = BASE_DIR / "data" / "db"
LOGS_DIR = BASE_DIR / "logs"

PROC_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "etl_pipeline.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("ETLPipeline")

DB_PATH = DB_DIR / "bluestock_mf.db"


def clean_nav_history(raw_file):
    """Clean nav_history.csv: parse dates, sort, drop invalid NAVs, deduplicate, forward-fill holidays/weekends."""
    logger.info("Cleaning 02_nav_history.csv...")
    df = pd.read_csv(raw_file)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "nav"])
    df = df[df["nav"] > 0]
    df = df.sort_values(["amfi_code", "date"]).drop_duplicates(subset=["amfi_code", "date"]).reset_index(drop=True)

    # Calendar Expansion per Scheme for Weekend/Holiday NAV Continuity
    cleaned_schemes = []
    min_date = df["date"].min()
    max_date = df["date"].max()
    full_date_range = pd.date_range(start=min_date, end=max_date, freq="D")

    for code, group in df.groupby("amfi_code"):
        scheme_name = group["scheme_name"].iloc[0] if "scheme_name" in group.columns else f"Scheme {code}"
        group_indexed = group.set_index("date").reindex(full_date_range)
        group_indexed["amfi_code"] = code
        group_indexed["scheme_name"] = scheme_name
        group_indexed["nav"] = group_indexed["nav"].ffill().bfill()
        group_indexed = group_indexed.reset_index().rename(columns={"index": "date"})
        cleaned_schemes.append(group_indexed)

    result_df = pd.concat(cleaned_schemes, ignore_index=True)
    result_df["date"] = result_df["date"].dt.strftime("%Y-%m-%d")
    return result_df


def clean_investor_transactions(raw_file):
    """Clean investor_transactions.csv: standardize types, validate amount > 0, dates, KYC status."""
    logger.info("Cleaning 08_investor_transactions.csv...")
    df = pd.read_csv(raw_file)
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    df = df.dropna(subset=["transaction_date", "amount_inr"])
    df = df[df["amount_inr"] > 0]

    # Standardize transaction types
    type_map = {
        "SIP": "SIP", "LUMPSUM": "Lumpsum", "REDEMPTION": "Redemption",
        "STP": "STP", "SWP": "SWP"
    }
    df["transaction_type"] = df["transaction_type"].str.upper().str.strip().map(lambda x: type_map.get(x, x))

    # Standardize KYC status
    kyc_map = {"VERIFIED": "Verified", "PENDING": "Pending", "REJECTED": "Rejected"}
    df["kyc_status"] = df["kyc_status"].astype(str).str.upper().str.strip().map(lambda x: kyc_map.get(x, x))

    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    return df.drop_duplicates().reset_index(drop=True)


def clean_scheme_performance(raw_file):
    """Clean scheme_performance.csv: numeric return validation, expense ratio range check."""
    logger.info("Cleaning 07_scheme_performance.csv...")
    df = pd.read_csv(raw_file)
    numeric_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "expense_ratio_pct", "aum_crore", "sharpe_ratio"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Expense ratio range check (0.1% to 2.5%)
    if "expense_ratio_pct" in df.columns:
        df["expense_ratio_pct"] = df["expense_ratio_pct"].clip(lower=0.10, upper=2.50)

    return df.drop_duplicates().reset_index(drop=True)


def clean_generic_dataset(file_path):
    """Clean generic datasets: trim strings, format date/month columns, deduplicate."""
    df = pd.read_csv(file_path)
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
        if "date" in col.lower() or "month" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
    return df.drop_duplicates().reset_index(drop=True)


def run_etl_cleaning():
    """Execute cleaning on all 10 Bluestock raw datasets and export to data/processed/."""
    logger.info("Running ETL Cleaning Phase...")
    
    cleaners = {
        "01_fund_master.csv": clean_generic_dataset,
        "02_nav_history.csv": clean_nav_history,
        "03_aum_by_fund_house.csv": clean_generic_dataset,
        "04_monthly_sip_inflows.csv": clean_generic_dataset,
        "05_category_inflows.csv": clean_generic_dataset,
        "06_industry_folio_count.csv": clean_generic_dataset,
        "07_scheme_performance.csv": clean_scheme_performance,
        "08_investor_transactions.csv": clean_investor_transactions,
        "09_portfolio_holdings.csv": clean_generic_dataset,
        "10_benchmark_indices.csv": clean_generic_dataset,
    }

    for filename, func in cleaners.items():
        raw_path = RAW_DIR / filename
        proc_path = PROC_DIR / filename
        if raw_path.exists():
            cleaned_df = func(raw_path)
            cleaned_df.to_csv(proc_path, index=False)
            logger.info(f"Cleaned {filename} -> {proc_path} ({len(cleaned_df)} rows)")
        else:
            logger.warning(f"Raw file {raw_path} missing.")


def build_sqlite_database():
    """Load cleaned datasets into SQLite database data/db/bluestock_mf.db."""
    logger.info(f"Populating SQLite Database at {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)

    table_mappings = [
        ("dim_fund", "01_fund_master.csv"),
        ("fact_nav", "02_nav_history.csv"),
        ("fact_aum", "03_aum_by_fund_house.csv"),
        ("fact_sip_inflows", "04_monthly_sip_inflows.csv"),
        ("fact_category_inflows", "05_category_inflows.csv"),
        ("fact_industry_folios", "06_industry_folio_count.csv"),
        ("fact_performance", "07_scheme_performance.csv"),
        ("fact_transactions", "08_investor_transactions.csv"),
        ("fact_portfolio_holdings", "09_portfolio_holdings.csv"),
        ("fact_benchmark", "10_benchmark_indices.csv"),
    ]

    # Generate dim_date
    nav_df = pd.read_csv(PROC_DIR / "02_nav_history.csv")
    nav_df["date"] = pd.to_datetime(nav_df["date"])
    full_dates = pd.date_range(nav_df["date"].min(), nav_df["date"].max(), freq="D")

    dim_date = pd.DataFrame({
        "date": full_dates.strftime("%Y-%m-%d"),
        "year": full_dates.year,
        "quarter": full_dates.quarter,
        "month": full_dates.month,
        "month_name": full_dates.strftime("%B"),
        "day": full_dates.day,
        "day_name": full_dates.strftime("%A"),
        "day_of_week": full_dates.dayofweek + 1,
        "is_weekend": np.where(full_dates.dayofweek >= 5, 1, 0)
    })
    dim_date.to_sql("dim_date", conn, if_exists="replace", index=False)
    logger.info(f"Loaded dim_date table ({len(dim_date)} rows)")

    for table_name, csv_file in table_mappings:
        csv_path = PROC_DIR / csv_file
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            logger.info(f"Loaded {table_name} table ({len(df)} rows)")

    conn.close()


def verify_row_count_parity():
    """Verify 100% row count parity between processed CSV files and SQLite database tables."""
    logger.info("Executing Row Count Parity Verification...")
    conn = sqlite3.connect(DB_PATH)

    table_mappings = [
        ("dim_fund", "01_fund_master.csv"),
        ("fact_nav", "02_nav_history.csv"),
        ("fact_aum", "03_aum_by_fund_house.csv"),
        ("fact_sip_inflows", "04_monthly_sip_inflows.csv"),
        ("fact_category_inflows", "05_category_inflows.csv"),
        ("fact_industry_folios", "06_industry_folio_count.csv"),
        ("fact_performance", "07_scheme_performance.csv"),
        ("fact_transactions", "08_investor_transactions.csv"),
        ("fact_portfolio_holdings", "09_portfolio_holdings.csv"),
        ("fact_benchmark", "10_benchmark_indices.csv"),
    ]

    parity_passed = True
    print("\n" + "=" * 85)
    print(f"{'Target SQL Table':<25} | {'Source CSV File':<28} | {'CSV Rows':<10} | {'DB Rows':<10} | Status")
    print("-" * 85)

    for table_name, csv_file in table_mappings:
        csv_path = PROC_DIR / csv_file
        csv_rows = len(pd.read_csv(csv_path)) if csv_path.exists() else 0
        db_rows = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]

        status = "PASSED" if csv_rows == db_rows else "FAILED"
        if status == "FAILED":
            parity_passed = False

        print(f"{table_name:<25} | {csv_file:<28} | {csv_rows:<10} | {db_rows:<10} | {status}")

    print("=" * 85)
    conn.close()

    if parity_passed:
        logger.info("[SUCCESS] All 10 database tables match source cleaned CSV row counts exactly!")
    else:
        logger.error("[FAILURE] Row count parity mismatch detected!")
        sys.exit(1)


def main():
    logger.info("Starting Master ETL Pipeline...")
    run_etl_cleaning()
    build_sqlite_database()
    verify_row_count_parity()
    logger.info("Master ETL Pipeline Finished Successfully.")


if __name__ == "__main__":
    main()
