"""
data_ingestion.py - Bluestock Mutual Fund Capstone Project Data Ingestion & Quality Audit

Loads all 10 official Bluestock CSV datasets, inspects structures (.shape, .dtypes, .head()),
audits data quality anomalies, explores Fund Master metadata, and validates AMFI scheme code coverage.
"""

import os
import sys
import logging
import pandas as pd

# Enforce UTF-8 standard output for cross-platform compatibility
sys.stdout.reconfigure(encoding="utf-8")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DataIngestionEngine")

BASE_DIR = os.path.dirname(__file__)
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")

# 10 Official Bluestock Capstone CSV Datasets
BLUESTOCK_DATASETS = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv"
]


def load_and_inspect_datasets() -> dict:
    """
    Loads all 10 provided Bluestock CSV datasets, prints shape, dtypes, head(), and audits anomalies.
    """
    dataframes = {}
    print("=" * 85)
    print(" BLUESTOCK MUTUAL FUND CAPSTONE PROJECT: DATA INGESTION & AUDIT ")
    print("=" * 85)

    for filename in BLUESTOCK_DATASETS:
        file_path = os.path.join(RAW_DIR, filename)

        if not os.path.exists(file_path):
            logger.error(f"Missing expected raw dataset: {file_path}")
            continue

        try:
            df = pd.read_csv(file_path)
            dataframes[filename] = df

            print(f"\n--- DATASET: {filename} ---")
            print(f"Dimensions (Rows, Columns): {df.shape}")
            print("\nData Types:")
            print(df.dtypes)
            print("\nHead (First 3 rows):")
            print(df.head(3))
            
            # Anomaly Checks
            missing_count = df.isnull().sum().to_dict()
            total_missing = sum(missing_count.values())
            dup_count = df.duplicated().sum()
            anomalies = []
            
            if total_missing > 0:
                cols_with_nulls = {k: v for k, v in missing_count.items() if v > 0}
                anomalies.append(f"Contains {total_missing} missing (NaN) values across columns: {cols_with_nulls}")
            if dup_count > 0:
                anomalies.append(f"Contains {dup_count} duplicate rows.")

            # Negative value check on numeric columns
            num_cols = df.select_dtypes(include=['float64', 'int64']).columns
            for col in num_cols:
                if col not in ["amfi_code", "sebi_category_code"]:
                    neg_cnt = (df[col] < 0).sum()
                    if neg_cnt > 0:
                        anomalies.append(f"Column '{col}' has {neg_cnt} negative values.")

            if anomalies:
                print("\n[!] Data Quality Anomalies Identified:")
                for anomaly in anomalies:
                    print(f"  - {anomaly}")
            else:
                print("\n[OK] Data Integrity Check: Passed (Zero missing values, duplicates, or out-of-bounds negatives).")

            print("-" * 85)

        except Exception as e:
            logger.error(f"Failed to load dataset {filename}: {e}")

    return dataframes


def explore_fund_master(fund_master_df: pd.DataFrame):
    """
    Explores 01_fund_master.csv: Fund Houses, Categories, Sub-Categories, Risk Grades,
    and documents the AMFI scheme code structure.
    """
    print("\n" + "=" * 85)
    print(" EXPLORATORY ANALYSIS: FUND MASTER & AMFI CODE STRUCTURE ")
    print("=" * 85)

    if fund_master_df is None or fund_master_df.empty:
        logger.error("01_fund_master.csv is empty or missing.")
        return

    print(f"\nTotal Mutual Fund Schemes in Master: {len(fund_master_df)}")

    print("\n1. Unique Fund Houses (AMCs):")
    amcs = sorted(fund_master_df["fund_house"].unique())
    for idx, amc in enumerate(amcs, 1):
        count = len(fund_master_df[fund_master_df["fund_house"] == amc])
        print(f"   {idx:2d}. {amc} ({count} schemes)")

    print("\n2. Unique Categories:")
    cats = sorted(fund_master_df["category"].unique())
    for idx, cat in enumerate(cats, 1):
        count = len(fund_master_df[fund_master_df["category"] == cat])
        print(f"   {idx}. {cat} ({count} schemes)")

    print("\n3. Unique Sub-Categories:")
    sub_cats = sorted(fund_master_df["sub_category"].unique())
    for idx, sub_cat in enumerate(sub_cats, 1):
        count = len(fund_master_df[fund_master_df["sub_category"] == sub_cat])
        print(f"   {idx:2d}. {sub_cat} ({count} schemes)")

    print("\n4. Unique Risk Grades / Categories:")
    risk_cats = sorted(fund_master_df["risk_category"].unique())
    for idx, rg in enumerate(risk_cats, 1):
        count = len(fund_master_df[fund_master_df["risk_category"] == rg])
        print(f"   {idx}. {rg} ({count} schemes)")

    print("\n5. AMFI Scheme Code Structure Overview:")
    print("   - AMFI (Association of Mutual Funds in India) assigns a 6-digit numeric code")
    print("     to uniquely identify each mutual fund scheme variant in India.")
    print("   - Separate codes are allocated for Direct vs Regular plans and Growth vs IDCW (Dividend) options.")
    print("   - Target Key Schemes Ingested from Live API:")
    print("       * 125497 : HDFC Top 100 Fund - Direct Plan - Growth")
    print("       * 119551 : SBI Bluechip Fund - Direct Plan - Growth")
    print("       * 120503 : ICICI Prudential Bluechip Fund - Direct Plan - Growth")
    print("       * 118632 : Nippon India Large Cap Fund - Direct Plan - Growth")
    print("       * 119092 : Axis Bluechip Fund - Direct Plan - Growth")
    print("       * 120841 : Kotak Bluechip Fund - Direct Plan - Growth")


def validate_amfi_codes(fund_master_df: pd.DataFrame, nav_history_df: pd.DataFrame):
    """
    Validates that every amfi_code in 01_fund_master.csv exists in 02_nav_history.csv.
    """
    print("\n" + "=" * 85)
    print(" VALIDATION: AMFI SCHEME CODE CROSS-COVERAGE AUDIT ")
    print("=" * 85)

    if fund_master_df is None or nav_history_df is None:
        logger.error("Validation failed: 01_fund_master.csv or 02_nav_history.csv not loaded.")
        return

    master_codes = set(fund_master_df["amfi_code"].unique())
    nav_codes = set(nav_history_df["amfi_code"].unique())

    missing_in_nav = master_codes - nav_codes
    extra_in_nav = nav_codes - master_codes

    print(f"Unique AMFI Codes in 01_fund_master.csv : {len(master_codes)}")
    print(f"Unique AMFI Codes in 02_nav_history.csv : {len(nav_codes)}")

    if not missing_in_nav:
        print("\n[OK] AMFI CODE COVERAGE AUDIT PASSED: 100% of fund_master AMFI codes exist in nav_history.")
    else:
        print(f"\n[!] COVERAGE AUDIT WARNING: {len(missing_in_nav)} scheme code(s) missing from nav_history:")
        for code in missing_in_nav:
            name = fund_master_df[fund_master_df["amfi_code"] == code]["scheme_name"].values[0]
            print(f"    - AMFI Code: {code} ({name})")

    if extra_in_nav:
        print(f"\n[i] Note: nav_history contains {len(extra_in_nav)} extra AMFI code(s) not listed in fund_master.")

    print("=" * 85)


def generate_data_quality_summary(dataframes: dict):
    """
    Prints a concise Data Quality Summary table across all ingested datasets.
    """
    print("\n" + "=" * 85)
    print(" DATA QUALITY SUMMARY REPORT ")
    print("=" * 85)
    
    summary_rows = []
    for filename in BLUESTOCK_DATASETS:
        if filename in dataframes:
            df = dataframes[filename]
            total_rows, total_cols = df.shape
            null_count = df.isnull().sum().sum()
            dup_count = df.duplicated().sum()
            status = "CLEAN" if null_count == 0 and dup_count == 0 else "NEEDS ATTENTION"
            summary_rows.append({
                "Dataset": filename,
                "Rows": total_rows,
                "Columns": total_cols,
                "Null Values": null_count,
                "Duplicates": dup_count,
                "Quality Status": status
            })

    summary_df = pd.DataFrame(summary_rows)
    print(summary_df.to_string(index=False))
    print("=" * 85)


def main():
    logger.info("Starting Data Ingestion & Audit for Bluestock Mutual Fund Datasets...")
    dataframes = load_and_inspect_datasets()

    fund_master_df = dataframes.get("01_fund_master.csv")
    nav_history_df = dataframes.get("02_nav_history.csv")

    if fund_master_df is not None:
        explore_fund_master(fund_master_df)

    if fund_master_df is not None and nav_history_df is not None:
        validate_amfi_codes(fund_master_df, nav_history_df)

    generate_data_quality_summary(dataframes)
    logger.info("Data Ingestion & Quality Audit Completed.")


if __name__ == "__main__":
    main()
