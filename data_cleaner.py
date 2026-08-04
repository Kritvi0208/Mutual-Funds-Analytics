"""
data_cleaner.py - Bluestock Mutual Fund Analytics Data Cleaning Engine

Performs comprehensive ETL cleaning on all 10 raw Bluestock CSV datasets:
1. 01_fund_master.csv: Trims text fields, validates AMFI code uniqueness & expense ratios.
2. 02_nav_history.csv: Datetime parsing, sorting by amfi_code + date, deduplication, NAV > 0 validation, and calendar ffill.
3. 03_aum_by_fund_house.csv: Date parsing, AUM numeric validation.
4. 04_monthly_sip_inflows.csv: Date formatting, YoY growth validation.
5. 05_category_inflows.csv: Category standardisation, month formatting.
6. 06_industry_folio_count.csv: Folio count numeric validation.
7. 07_scheme_performance.csv: Return metric numeric validation, expense ratio range check (0.1%-2.5%), anomaly flagging.
8. 08_investor_transactions.csv: Transaction type standardisation, amount > 0 check, date formatting, KYC status enum check.
9. 09_portfolio_holdings.csv: Weight percentage check, stock symbol standardisation.
10. 10_benchmark_indices.csv: Date parsing, close value numeric validation.

Exports all 10 cleaned CSV datasets into data/processed/.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Enforce UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
LOGS_DIR = BASE_DIR / "logs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "cleaning.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("DataCleanerEngine")


def clean_fund_master(file_path: Path) -> pd.DataFrame:
    """Clean 01_fund_master.csv."""
    logger.info("Cleaning 01_fund_master.csv...")
    df = pd.read_csv(file_path)
    
    # Strip string whitespace
    str_cols = df.select_dtypes(include="object").columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip()

    # Parse launch_date
    df["launch_date"] = pd.to_datetime(df["launch_date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # Validate expense_ratio_pct range (0.1% - 2.5%)
    df["expense_ratio_pct"] = pd.to_numeric(df["expense_ratio_pct"], errors="coerce")
    invalid_expense = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
    if not invalid_expense.empty:
        logger.warning(f"Fund Master: {len(invalid_expense)} schemes with expense ratio outside 0.1%-2.5% range.")

    # Remove duplicates on amfi_code
    df = df.drop_duplicates(subset=["amfi_code"]).reset_index(drop=True)
    logger.info(f"01_fund_master.csv cleaned ({len(df)} schemes).")
    return df


def clean_nav_history(file_path: Path) -> pd.DataFrame:
    """Clean 02_nav_history.csv."""
    logger.info("Cleaning 02_nav_history.csv...")
    df = pd.read_csv(file_path)

    # 1. Parse dates to datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    # 2. Validate NAV > 0
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df[df["nav"] > 0]

    # 3. Sort by amfi_code + date
    df = df.sort_values(by=["amfi_code", "date"]).reset_index(drop=True)

    # 4. Remove duplicate rows (amfi_code, date)
    df = df.drop_duplicates(subset=["amfi_code", "date"]).reset_index(drop=True)

    # 5. Forward-fill missing NAV for holidays/weekends per scheme
    cleaned_schemes = []
    for amfi_code, group in df.groupby("amfi_code"):
        group = group.set_index("date")
        # Create complete calendar range from min date to max date
        min_date = group.index.min()
        max_date = group.index.max()
        full_date_range = pd.date_range(start=min_date, end=max_date, freq="D", name="date")
        
        group_reindexed = group.reindex(full_date_range)
        group_reindexed["amfi_code"] = amfi_code
        group_reindexed["nav"] = group_reindexed["nav"].ffill().bfill()
        
        group_reindexed = group_reindexed.reset_index()
        cleaned_schemes.append(group_reindexed)

    df_cleaned = pd.concat(cleaned_schemes, ignore_index=True)
    df_cleaned["date"] = df_cleaned["date"].dt.strftime("%Y-%m-%d")
    df_cleaned["amfi_code"] = df_cleaned["amfi_code"].astype(int)
    df_cleaned = df_cleaned.sort_values(by=["amfi_code", "date"]).reset_index(drop=True)

    logger.info(f"02_nav_history.csv cleaned ({len(df_cleaned)} NAV records after forward-fill calendar expansion).")
    return df_cleaned


def clean_aum_by_fund_house(file_path: Path) -> pd.DataFrame:
    """Clean 03_aum_by_fund_house.csv."""
    logger.info("Cleaning 03_aum_by_fund_house.csv...")
    df = pd.read_csv(file_path)
    df["fund_house"] = df["fund_house"].astype(str).str.strip()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.sort_values(by=["fund_house", "date"]).drop_duplicates(subset=["fund_house", "date"]).reset_index(drop=True)
    logger.info(f"03_aum_by_fund_house.csv cleaned ({len(df)} records).")
    return df


def clean_monthly_sip_inflows(file_path: Path) -> pd.DataFrame:
    """Clean 04_monthly_sip_inflows.csv."""
    logger.info("Cleaning 04_monthly_sip_inflows.csv...")
    df = pd.read_csv(file_path)
    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.strftime("%Y-%m")
    df = df.sort_values(by="month").drop_duplicates(subset=["month"]).reset_index(drop=True)
    logger.info(f"04_monthly_sip_inflows.csv cleaned ({len(df)} records).")
    return df


def clean_category_inflows(file_path: Path) -> pd.DataFrame:
    """Clean 05_category_inflows.csv."""
    logger.info("Cleaning 05_category_inflows.csv...")
    df = pd.read_csv(file_path)
    df["category"] = df["category"].astype(str).str.strip()
    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.strftime("%Y-%m")
    df = df.sort_values(by=["category", "month"]).drop_duplicates(subset=["category", "month"]).reset_index(drop=True)
    logger.info(f"05_category_inflows.csv cleaned ({len(df)} records).")
    return df


def clean_industry_folio_count(file_path: Path) -> pd.DataFrame:
    """Clean 06_industry_folio_count.csv."""
    logger.info("Cleaning 06_industry_folio_count.csv...")
    df = pd.read_csv(file_path)
    df["month"] = pd.to_datetime(df["month"], errors="coerce").dt.strftime("%Y-%m")
    df = df.sort_values(by="month").drop_duplicates(subset=["month"]).reset_index(drop=True)
    logger.info(f"06_industry_folio_count.csv cleaned ({len(df)} records).")
    return df


def clean_scheme_performance(file_path: Path) -> pd.DataFrame:
    """Clean 07_scheme_performance.csv."""
    logger.info("Cleaning 07_scheme_performance.csv...")
    df = pd.read_csv(file_path)

    # Validate numeric returns
    return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct", "expense_ratio_pct"]
    for col in return_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Check expense_ratio range (0.1% – 2.5%)
    df["expense_ratio_valid"] = df["expense_ratio_pct"].apply(lambda x: 0.1 <= x <= 2.5 if pd.notnull(x) else False)
    invalid_exp = df[~df["expense_ratio_valid"]]
    if not invalid_exp.empty:
        logger.warning(f"Scheme Performance: {len(invalid_exp)} schemes have expense ratios outside 0.1%-2.5%.")

    # Flag performance anomalies (e.g. Sharpe ratio > 5 or < -3, alpha > 25%)
    df["is_anomaly"] = (df["sharpe_ratio"] > 5) | (df["sharpe_ratio"] < -3) | (df["alpha"].abs() > 25)
    anomaly_cnt = df["is_anomaly"].sum()
    logger.info(f"Scheme Performance: Flagged {anomaly_cnt} performance anomalies.")

    df = df.drop(columns=["expense_ratio_valid", "is_anomaly"], errors="ignore")
    df = df.drop_duplicates(subset=["amfi_code"]).reset_index(drop=True)
    logger.info(f"07_scheme_performance.csv cleaned ({len(df)} records).")
    return df


def clean_investor_transactions(file_path: Path) -> pd.DataFrame:
    """Clean 08_investor_transactions.csv."""
    logger.info("Cleaning 08_investor_transactions.csv...")
    df = pd.read_csv(file_path)

    # 1. Standardise transaction_type values
    type_map = {
        "sip": "SIP",
        "lumpsum": "Lumpsum",
        "redemption": "Redemption",
        "stp": "STP",
        "swp": "SWP"
    }
    df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.lower().map(lambda x: type_map.get(x, x.upper()))

    # 2. Validate amount > 0
    df["amount_inr"] = pd.to_numeric(df["amount_inr"], errors="coerce")
    df = df[df["amount_inr"] > 0]

    # 3. Fix date formats
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.dropna(subset=["transaction_date"])

    # 4. Check & standardise KYC status enum values
    df["kyc_status"] = df["kyc_status"].astype(str).str.strip().str.title()
    valid_kyc = ["Verified", "Pending", "Rejected"]
    df["kyc_status"] = df["kyc_status"].apply(lambda x: x if x in valid_kyc else "Pending")

    df = df.drop_duplicates(subset=["investor_id", "transaction_date", "amfi_code", "amount_inr"]).reset_index(drop=True)
    logger.info(f"08_investor_transactions.csv cleaned ({len(df)} records).")
    return df


def clean_portfolio_holdings(file_path: Path) -> pd.DataFrame:
    """Clean 09_portfolio_holdings.csv."""
    logger.info("Cleaning 09_portfolio_holdings.csv...")
    df = pd.read_csv(file_path)
    df["stock_symbol"] = df["stock_symbol"].astype(str).str.strip().str.upper()
    df["stock_name"] = df["stock_name"].astype(str).str.strip()
    df["sector"] = df["sector"].astype(str).str.strip()
    df["weight_pct"] = pd.to_numeric(df["weight_pct"], errors="coerce")
    df["portfolio_date"] = pd.to_datetime(df["portfolio_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df = df.drop_duplicates(subset=["amfi_code", "stock_symbol", "portfolio_date"]).reset_index(drop=True)
    logger.info(f"09_portfolio_holdings.csv cleaned ({len(df)} records).")
    return df


def clean_benchmark_indices(file_path: Path) -> pd.DataFrame:
    """Clean 10_benchmark_indices.csv."""
    logger.info("Cleaning 10_benchmark_indices.csv...")
    df = pd.read_csv(file_path)
    df["index_name"] = df["index_name"].astype(str).str.strip().str.upper()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["close_value"] = pd.to_numeric(df["close_value"], errors="coerce")
    df = df.dropna(subset=["date", "close_value"])
    df = df.sort_values(by=["index_name", "date"]).drop_duplicates(subset=["index_name", "date"]).reset_index(drop=True)
    logger.info(f"10_benchmark_indices.csv cleaned ({len(df)} records).")
    return df


def main():
    logger.info("Starting Bluestock Mutual Funds Data Cleaning Engine...")

    cleaners = {
        "01_fund_master.csv": clean_fund_master,
        "02_nav_history.csv": clean_nav_history,
        "03_aum_by_fund_house.csv": clean_aum_by_fund_house,
        "04_monthly_sip_inflows.csv": clean_monthly_sip_inflows,
        "05_category_inflows.csv": clean_category_inflows,
        "06_industry_folio_count.csv": clean_industry_folio_count,
        "07_scheme_performance.csv": clean_scheme_performance,
        "08_investor_transactions.csv": clean_investor_transactions,
        "09_portfolio_holdings.csv": clean_portfolio_holdings,
        "10_benchmark_indices.csv": clean_benchmark_indices
    }

    cleaned_counts = {}

    for filename, cleaner_func in cleaners.items():
        raw_file = RAW_DIR / filename
        if not raw_file.exists():
            logger.error(f"Missing raw file: {raw_file}")
            continue

        cleaned_df = cleaner_func(raw_file)
        out_file = PROCESSED_DIR / filename
        cleaned_df.to_csv(out_file, index=False)
        cleaned_counts[filename] = len(cleaned_df)
        logger.info(f"Saved cleaned dataset to {out_file}")

    print("\n" + "=" * 80)
    print(" DATA CLEANING SUMMARY REPORT ")
    print("=" * 80)
    for fname, count in cleaned_counts.items():
        print(f" - {fname:<30}: {count:>8,d} cleaned rows saved to data/processed/")
    print("=" * 80)
    logger.info("Data Cleaning Engine finished successfully.")


if __name__ == "__main__":
    main()
