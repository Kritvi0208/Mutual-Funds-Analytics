"""
data_loader.py - SQLite Star Schema Loader & Parity Verification Engine

Loads cleaned CSV datasets from data/processed/ into SQLite database bluestock_mf.db
using SQLAlchemy create_engine and df.to_sql(), populating dim_date dimension, and
verifying row count parity.
"""

import sys
import logging
from pathlib import Path
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

# Enforce UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
LOGS_DIR = BASE_DIR / "logs"
DB_PATH = BASE_DIR / "sql" / "bluestock_mf.db"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "loader.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("DataLoaderEngine")


def initialize_database():
    """Execute schema.sql to construct SQLite tables."""
    logger.info(f"Initializing SQLite database at {DB_PATH} using schema.sql...")
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.close()
    logger.info("Database schema initialized successfully.")


def populate_dim_date(engine):
    """Generate and load comprehensive calendar dimension (dim_date)."""
    logger.info("Generating and populating dim_date calendar dimension...")
    # Get min and max date across processed datasets
    nav_df = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv")
    min_date = pd.to_datetime(nav_df["date"]).min()
    max_date = pd.to_datetime(nav_df["date"]).max()

    date_range = pd.date_range(start="2020-01-01", end=max_date + pd.Timedelta(days=365), freq="D")
    dim_date = pd.DataFrame({
        "date": date_range.strftime("%Y-%m-%d"),
        "year": date_range.year,
        "quarter": date_range.quarter,
        "month": date_range.month,
        "month_name": date_range.strftime("%B"),
        "day": date_range.day,
        "day_name": date_range.strftime("%A"),
        "day_of_week": date_range.dayofweek + 1,
        "is_weekend": date_range.dayofweek.isin([5, 6]).astype(int)
    })

    dim_date.to_sql("dim_date", con=engine, if_exists="replace", index=False)
    logger.info(f"dim_date populated with {len(dim_date)} calendar dates.")


def load_datasets_to_sqlite(engine) -> dict:
    """Load cleaned CSV datasets into corresponding SQLite Star Schema tables."""
    table_mappings = {
        "01_fund_master.csv": "dim_fund",
        "02_nav_history.csv": "fact_nav",
        "03_aum_by_fund_house.csv": "fact_aum",
        "04_monthly_sip_inflows.csv": "fact_sip_inflows",
        "05_category_inflows.csv": "fact_category_inflows",
        "06_industry_folio_count.csv": "fact_industry_folios",
        "07_scheme_performance.csv": "fact_performance",
        "08_investor_transactions.csv": "fact_transactions",
        "09_portfolio_holdings.csv": "fact_portfolio_holdings",
        "10_benchmark_indices.csv": "fact_benchmark"
    }

    parity_audit = {}

    for csv_name, table_name in table_mappings.items():
        csv_path = PROCESSED_DIR / csv_name
        if not csv_path.exists():
            logger.error(f"Missing processed CSV file: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        csv_rows = len(df)

        # Load into SQLite
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)

        # Verify DB row count parity
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            db_rows = cur.fetchone()[0]

        is_parity = (csv_rows == db_rows)
        parity_audit[table_name] = {
            "csv_file": csv_name,
            "csv_rows": csv_rows,
            "db_rows": db_rows,
            "parity_match": is_parity
        }

        status_str = "MATCH [✓]" if is_parity else "MISMATCH [!]"
        logger.info(f"Loaded {table_name}: CSV={csv_rows:,} | DB={db_rows:,} -> {status_str}")

    return parity_audit


def print_parity_report(parity_audit: dict):
    """Print verification summary report comparing CSV vs Database row counts."""
    print("\n" + "=" * 85)
    print(" ROW COUNT PARITY VERIFICATION SUMMARY (CSV vs SQLITE DB) ")
    print("=" * 85)
    print(f"{'Target SQL Table':<25} | {'Source CSV File':<30} | {'CSV Rows':<10} | {'DB Rows':<10} | {'Status':<8}")
    print("-" * 85)

    all_passed = True
    for table_name, meta in parity_audit.items():
        status = "PASSED" if meta["parity_match"] else "FAILED"
        if not meta["parity_match"]:
            all_passed = False
        print(f"{table_name:<25} | {meta['csv_file']:<30} | {meta['csv_rows']:<10,d} | {meta['db_rows']:<10,d} | {status:<8}")

    print("=" * 85)
    if all_passed:
        print("[SUCCESS] All 10 database tables match source cleaned CSV row counts exactly!")
    else:
        print("[WARNING] Row count mismatch detected in database tables.")
    print("=" * 85)


def main():
    logger.info("Starting Bluestock Mutual Funds SQLite Database Loader...")
    engine = create_engine(f"sqlite:///{DB_PATH}")

    initialize_database()
    populate_dim_date(engine)
    parity_audit = load_datasets_to_sqlite(engine)
    print_parity_report(parity_audit)

    logger.info("Database Loader Engine finished successfully.")


if __name__ == "__main__":
    main()
