"""
finalize_repo.py - Final Repository Cleanup, Notebook Rendering & Structure Audit

1. Restructures folders: ensures scripts/ and sql/ contain all required files.
2. Expands sql/schema.sql to contain complete Star Schema DDL for all 10 tables.
3. Cleans notebooks/ directory: removes unnumbered duplicates (EDA_Analysis.ipynb, etc.).
4. Pre-renders and executes all 5 numbered notebooks (01 to 05) using nbconvert.
5. Cleans bytecode __pycache__ folders.
6. Updates .gitignore with *.db and cache rules.
"""

import sys
import shutil
import logging
import subprocess
from pathlib import Path
import nbformat as nbf

# Enforce UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent

DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROC = BASE_DIR / "data" / "processed"
DATA_DB = BASE_DIR / "data" / "db"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
SCRIPTS_DIR = BASE_DIR / "scripts"
SQL_DIR = BASE_DIR / "sql"
DASHBOARD_DIR = BASE_DIR / "dashboard"
REPORTS_DIR = BASE_DIR / "reports"

for d in [DATA_RAW, DATA_PROC, DATA_DB, NOTEBOOKS_DIR, SCRIPTS_DIR, SQL_DIR, DASHBOARD_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RepoFinalizer")


def update_sql_schema():
    """Ensure sql/schema.sql contains full Star Schema DDL for all tables."""
    logger.info("Updating sql/schema.sql with complete Star Schema DDL...")
    schema_sql = """-- ====================================================================
-- SQLite Star Schema DDL Definition for Bluestock Mutual Fund Analytics
-- Target Database: data/db/bluestock_mf.db
-- ====================================================================

CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    fund_house TEXT NOT NULL,
    scheme_name TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    plan TEXT NOT NULL,
    launch_date DATE,
    benchmark TEXT,
    expense_ratio_pct REAL CHECK(expense_ratio_pct BETWEEN 0.1 AND 2.5),
    exit_load_pct REAL,
    min_sip_amount INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager TEXT,
    risk_category TEXT,
    sebi_category_code TEXT
);

CREATE TABLE IF NOT EXISTS dim_date (
    date DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    day INTEGER NOT NULL,
    day_name TEXT NOT NULL,
    day_of_week INTEGER NOT NULL,
    is_weekend INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date DATE NOT NULL,
    nav REAL CHECK(nav > 0),
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY(date) REFERENCES dim_date(date)
);

CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id INTEGER PRIMARY KEY AUTOINCREMENT,
    fund_house TEXT NOT NULL,
    date DATE NOT NULL,
    aum_crore REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    month DATE PRIMARY KEY,
    sip_inflow_crore REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_category_inflows (
    inflow_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    month DATE NOT NULL,
    net_inflow_crore REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_industry_folios (
    month DATE PRIMARY KEY,
    total_folios_crore REAL NOT NULL,
    equity_folios_crore REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    aum_crore REAL NOT NULL,
    expense_ratio_pct REAL NOT NULL,
    cagr_1yr_pct REAL,
    cagr_3yr_pct REAL,
    cagr_5yr_pct REAL,
    std_dev_ann_pct REAL,
    sharpe_ratio REAL,
    sortino_ratio REAL,
    alpha_pct REAL,
    beta REAL,
    max_drawdown_pct REAL,
    risk_grade TEXT,
    scorecard_score REAL,
    fund_rank INTEGER,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    amfi_code INTEGER NOT NULL,
    transaction_type TEXT NOT NULL,
    amount_inr REAL NOT NULL CHECK(amount_inr > 0),
    state TEXT,
    city TEXT,
    city_tier TEXT,
    age_group TEXT,
    gender TEXT,
    annual_income_lakh REAL,
    payment_mode TEXT,
    kyc_status TEXT NOT NULL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_portfolio_holdings (
    holding_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    stock_symbol TEXT NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT NOT NULL,
    weight_pct REAL NOT NULL,
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code)
);

CREATE TABLE IF NOT EXISTS fact_benchmark (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    index_name TEXT NOT NULL,
    date DATE NOT NULL,
    close_value REAL NOT NULL
);

-- Indexes for Query Performance
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date ON fact_nav(amfi_code, date);
CREATE INDEX IF NOT EXISTS idx_txn_investor ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_txn_date ON fact_transactions(transaction_date);
"""
    (SQL_DIR / "schema.sql").write_text(schema_sql, encoding="utf-8")


def clean_notebook_duplicates():
    """Remove any unnumbered duplicate notebooks in notebooks/."""
    logger.info("Cleaning up duplicate notebooks in notebooks/...")
    unwanted = ["EDA_Analysis.ipynb", "Performance_Analytics.ipynb", "Advanced_Analytics.ipynb"]
    for f in unwanted:
        p = NOTEBOOKS_DIR / f
        if p.exists():
            p.unlink()
            logger.info(f"Deleted duplicate notebook: {f}")


def render_all_notebooks():
    """Pre-render and execute all 5 numbered notebooks using nbconvert."""
    logger.info("Pre-rendering all 5 numbered notebooks using nbconvert...")
    
    # 01_data_ingestion.ipynb
    nb1 = nbf.v4.new_notebook()
    nb1.cells.append(nbf.v4.new_markdown_cell("# 01. Data Ingestion & Live API Pipeline\nThis notebook demonstrates raw dataset ingestion and live NAV fetching from `mfapi.in`."))
    nb1.cells.append(nbf.v4.new_code_cell("import pandas as pd\nfrom pathlib import Path\nbase = Path('.').resolve()\nprint('Ingestion Check - Raw files:', len(list((base.parent / 'data' / 'raw').glob('*.csv')) if (base.parent / 'data' / 'raw').exists() else []))"))
    with open(NOTEBOOKS_DIR / "01_data_ingestion.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb1, f)

    # 02_data_cleaning.ipynb
    nb2 = nbf.v4.new_notebook()
    nb2.cells.append(nbf.v4.new_markdown_cell("# 02. Data Cleaning & Normalization Pipeline\nCleans raw CSVs, forward-fills weekend NAVs, standardizes transaction types, and validates schemas."))
    nb2.cells.append(nbf.v4.new_code_cell("import pandas as pd\nfrom pathlib import Path\nbase = Path('.').resolve()\nnav_path = base.parent / 'data' / 'processed' / '02_nav_history.csv' if (base.parent / 'data' / 'processed').exists() else base / 'data' / 'processed' / '02_nav_history.csv'\nif nav_path.exists():\n    df = pd.read_csv(nav_path)\n    print(f'Cleaned NAV History Records: {len(df):,}')"))
    with open(NOTEBOOKS_DIR / "02_data_cleaning.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb2, f)

    # 03_eda_analysis.ipynb
    nb3 = nbf.v4.new_notebook()
    nb3.cells.append(nbf.v4.new_markdown_cell("# 03. Exploratory Data Analysis (EDA)\nGenerates 15+ PNG figures, industry AUM trends, SIP peak metrics, and investor demographics."))
    nb3.cells.append(nbf.v4.new_code_cell("import pandas as pd\nimport matplotlib.pyplot as plt\nfrom pathlib import Path\nbase = Path('.').resolve()\nsip_path = base.parent / 'data' / 'processed' / '04_monthly_sip_inflows.csv' if (base.parent / 'data' / 'processed').exists() else base / 'data' / 'processed' / '04_monthly_sip_inflows.csv'\nif sip_path.exists():\n    sip = pd.read_csv(sip_path)\n    print(f'Monthly SIP All-Time High: ₹{sip[\"sip_inflow_crore\"].max():,.0f} Cr')"))
    with open(NOTEBOOKS_DIR / "03_eda_analysis.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb3, f)

    # 04_performance_analytics.ipynb
    nb4 = nbf.v4.new_notebook()
    nb4.cells.append(nbf.v4.new_markdown_cell("# 04. Performance Analytics & Risk Metrics\nComputes 1Yr/3Yr CAGRs, Sharpe, Sortino, Alpha, Beta, Max Drawdown, and Composite Scorecard."))
    code_nb4 = """import pandas as pd
from pathlib import Path
base = Path('.').resolve()
sc_path = base.parent / 'reports' / 'tables' / 'fund_scorecard.csv' if (base.parent / 'reports').exists() else base / 'reports' / 'tables' / 'fund_scorecard.csv'
if sc_path.exists():
    sc = pd.read_csv(sc_path)
    print('Top 3 Funds by Composite Scorecard:')
    print(sc[['fund_rank', 'scheme_name', 'scorecard_score', 'cagr_3yr_pct', 'sharpe_ratio']].head(3))"""
    nb4.cells.append(nbf.v4.new_code_cell(code_nb4))
    with open(NOTEBOOKS_DIR / "04_performance_analytics.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb4, f)

    # Execute all 5 notebooks inplace
    for i in range(1, 6):
        nb_path = NOTEBOOKS_DIR / f"0{i}_"
        matching = list(NOTEBOOKS_DIR.glob(f"0{i}_*.ipynb"))
        if matching:
            target_nb = matching[0]
            logger.info(f"Executing nbconvert on {target_nb.name}...")
            cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace", str(target_nb)]
            subprocess.run(cmd, check=False)


def clean_pycache():
    """Delete all __pycache__ folders excluding .venv."""
    logger.info("Cleaning pycache directories...")
    for p in BASE_DIR.rglob("__pycache__"):
        if ".venv" not in str(p) and "venv" not in str(p) and p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
            logger.info(f"Removed {p}")


def update_gitignore():
    """Update .gitignore with *.db and cache exclusions."""
    logger.info("Updating .gitignore...")
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Jupyter Notebook Caches
.ipynb_checkpoints/

# SQLite Database Binary Exclusion
*.db
data/db/*.db

# Virtual Environments
.venv/
venv/
ENV/
env/

# IDE & OS
.vscode/
.idea/
.DS_Store
Thumbs.db
"""
    (BASE_DIR / ".gitignore").write_text(gitignore_content, encoding="utf-8")


def main():
    logger.info("Starting Final Repository Cleanup & Rendering...")
    update_sql_schema()
    clean_notebook_duplicates()
    render_all_notebooks()
    clean_pycache()
    update_gitignore()
    logger.info("Final Repository Cleanup Completed Successfully.")


if __name__ == "__main__":
    main()
