"""
data_ingestion.py - Bluestock Mutual Fund Capstone Project Data Ingestion & Quality Audit

Production ETL engine that loads all 10 official Bluestock CSV datasets, inspects structures,
performs schema validation, audits quality anomalies, explores Fund Master metadata,
validates AMFI scheme code coverage, and outputs cleaned data & quality reports.
"""

import sys
import time
import logging
from pathlib import Path
import pandas as pd

# Enforce UTF-8 standard output for cross-platform compatibility
sys.stdout.reconfigure(encoding="utf-8")

# Constants
DEFAULT_ENCODING = "utf-8"
FALLBACK_ENCODING = "latin1"

# Directory hierarchy setup using pathlib
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Create required directory structure automatically
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure Logging (StreamHandler + FileHandler)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "ingestion.log", encoding=DEFAULT_ENCODING)
    ]
)
logger = logging.getLogger("DataIngestionEngine")

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

# Essential Mandatory Columns for Resilient Schema Auditing
MANDATORY_COLUMNS = {
    "01_fund_master.csv": ["amfi_code", "scheme_name", "fund_house"],
    "02_nav_history.csv": ["amfi_code", "date", "nav"],
    "03_aum_by_fund_house.csv": ["date", "fund_house", "aum_crore"],
    "04_monthly_sip_inflows.csv": ["month", "sip_inflow_crore"],
    "05_category_inflows.csv": ["month", "category", "net_inflow_crore"],
    "06_industry_folio_count.csv": ["month", "total_folios_crore"],
    "07_scheme_performance.csv": ["amfi_code", "scheme_name"],
    "08_investor_transactions.csv": ["investor_id", "transaction_date", "amfi_code"],
    "09_portfolio_holdings.csv": ["amfi_code", "stock_symbol"],
    "10_benchmark_indices.csv": ["date", "index_name", "close_value"]
}


def load_and_inspect_datasets() -> dict:
    """
    Loads all 10 provided Bluestock CSV datasets, parses date columns, prints shape,
    dtypes, memory footprint, head(), audits schema & anomalies, and exports cleaned CSVs.
    """
    dataframes = {}
    print("=" * 85)
    print(" BLUESTOCK MUTUAL FUND CAPSTONE PROJECT: DATA INGESTION & AUDIT ")
    print("=" * 85)

    for filename in BLUESTOCK_DATASETS:
        file_path = RAW_DIR / filename

        try:
            # Read CSV with encoding fallback using defined constants
            try:
                df = pd.read_csv(file_path, encoding=DEFAULT_ENCODING)
            except UnicodeDecodeError:
                df = pd.read_csv(file_path, encoding=FALLBACK_ENCODING)

            # Auto-detect and parse date/month columns to datetime
            date_cols = [col for col in df.columns if "date" in col.lower() or "month" in col.lower()]
            for col in date_cols:
                df[col] = pd.to_datetime(df[col], errors="coerce")

            dataframes[filename] = df

            # Memory footprint calculation
            memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
            logger.info(f"{filename} loaded successfully ({df.shape[0]} rows, {df.shape[1]} columns, {memory_mb:.2f} MB)")

            print(f"\n--- DATASET: {filename} ---")
            print(f"Dimensions (Rows, Columns): {df.shape}")
            print(f"Memory Footprint           : {memory_mb:.2f} MB")
            print("\nData Types:")
            print(df.dtypes)
            print("\nHead (First 3 rows):")
            print(df.head(3))

            # Mandatory Schema & Extra Columns Audit
            mandatory = MANDATORY_COLUMNS.get(filename, [])
            if mandatory:
                missing_cols = set(mandatory) - set(df.columns)
                if missing_cols:
                    logger.warning(f"{filename}: Missing mandatory columns {missing_cols}")
                extra_cols = set(df.columns) - set(mandatory)
                if extra_cols:
                    logger.info(f"{filename}: Additional schema columns detected: {len(extra_cols)}")

            # Anomaly Checks & Missing Percentage Calculation
            null_series = df.isnull().sum()
            total_null = null_series.sum()
            total_cells = df.size
            null_pct = (total_null / total_cells * 100) if total_cells > 0 else 0.0
            dup_count = df.duplicated().sum()
            anomalies = []

            if total_null > 0:
                cols_with_nulls = {k: v for k, v in null_series.to_dict().items() if v > 0}
                anomalies.append(f"Contains {total_null} missing (NaN) values ({null_pct:.2f}% of cells) across: {cols_with_nulls}")
            if dup_count > 0:
                anomalies.append(f"Contains {dup_count} duplicate rows.")

            # Detect all numeric columns for negative value inspection
            num_cols = df.select_dtypes(include="number").columns
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

            # Save processed dataset copy
            processed_path = PROCESSED_DIR / filename
            df.to_csv(processed_path, index=False)
            logger.info(f"Saved processed dataset to {processed_path}")

            print("-" * 85)

        except FileNotFoundError:
            logger.error(f"{filename} not found at path: {file_path}")
        except pd.errors.ParserError:
            logger.error(f"CSV parsing failed for {filename}.")
        except Exception as e:
            logger.exception(f"Unexpected error loading {filename}: {e}")

    return dataframes


def explore_fund_master(fund_master_df: pd.DataFrame):
    """
    Explores 01_fund_master.csv: Fund Houses, Categories, Sub-Categories, Risk Grades,
    checks for duplicate AMFI codes, and documents the AMFI scheme code structure.
    """
    print("\n" + "=" * 85)
    print(" EXPLORATORY ANALYSIS: FUND MASTER & AMFI CODE STRUCTURE ")
    print("=" * 85)

    if fund_master_df is None or fund_master_df.empty:
        logger.error("01_fund_master.csv is empty or missing.")
        return

    print(f"\nTotal Mutual Fund Schemes in Master: {len(fund_master_df)}")

    # Check for Duplicate AMFI Codes in Fund Master
    duplicate_codes = fund_master_df["amfi_code"].duplicated().sum()
    if duplicate_codes > 0:
        logger.warning(f"{duplicate_codes} duplicate AMFI codes detected in fund_master.")
    else:
        print("[OK] AMFI Code Uniqueness Check: Passed (Zero duplicate AMFI codes in Master).")

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
    Prints and exports a concise Data Quality Summary table across all ingested datasets
    to both CSV and Excel (.xlsx) formats.
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
            total_cells = df.size
            null_pct = (null_count / total_cells * 100) if total_cells > 0 else 0.0
            dup_count = df.duplicated().sum()
            status = (
                "CLEAN"
                if null_count == 0 and dup_count == 0
                else "NEEDS ATTENTION"
            )
            summary_rows.append({
                "Dataset": filename,
                "Rows": total_rows,
                "Columns": total_cols,
                "Null Values": null_count,
                "Null Pct": f"{null_pct:.2f}%",
                "Duplicates": dup_count,
                "Quality Status": status
            })

    summary_df = pd.DataFrame(summary_rows)

    # Export quality summary to CSV and Excel
    csv_report_path = REPORTS_DIR / "data_quality_summary.csv"
    excel_report_path = REPORTS_DIR / "data_quality_summary.xlsx"

    summary_df.to_csv(csv_report_path, index=False)
    logger.info(f"Exported quality summary CSV to {csv_report_path}")

    try:
        summary_df.to_excel(excel_report_path, index=False)
        logger.info(f"Exported quality summary Excel report to {excel_report_path}")
    except Exception as e:
        logger.warning(f"Could not export Excel report: {e}")

    print(summary_df.to_string(index=False))
    print("=" * 85)


def main():
    """
    Execute the complete ETL ingestion, schema audit, validation, and reporting workflow.
    """
    start_time = time.time()
    logger.info("Starting Data Ingestion & Audit for Bluestock Mutual Fund Datasets...")

    dataframes = load_and_inspect_datasets()

    fund_master_df = dataframes.get("01_fund_master.csv")
    nav_history_df = dataframes.get("02_nav_history.csv")

    if fund_master_df is not None:
        explore_fund_master(fund_master_df)

    if fund_master_df is not None and nav_history_df is not None:
        validate_amfi_codes(fund_master_df, nav_history_df)

    generate_data_quality_summary(dataframes)

    elapsed = time.time() - start_time
    logger.info(f"Data Ingestion & Quality Audit Completed in {elapsed:.2f} seconds.")


if __name__ == "__main__":
    main()
