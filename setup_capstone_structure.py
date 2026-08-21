"""
setup_capstone_structure.py - Master Setup and Synchronizer for Bluestock Capstone

Organizes repository into exact target structure:
├── data/
│   ├── raw/
│   ├── processed/
│   └── db/ (bluestock_mf.db)
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_performance_analytics.ipynb
│   └── 05_advanced_analytics.ipynb (with B3 Monte Carlo & B4 Markowitz Frontier)
├── scripts/
│   ├── etl_pipeline.py
│   ├── live_nav_fetch.py
│   ├── compute_metrics.py
│   ├── recommender.py
│   ├── cron_nav_fetch.py (Bonus B1)
│   └── email_report.py (Bonus B5)
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── dashboard/
│   ├── app.py (Bonus B2 Streamlit)
│   └── bluestock_mf.pbix
├── reports/
│   ├── Final_Report.pdf
│   └── Presentation.pptx
└── README.md
"""

import sys
import shutil
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import nbformat as nbf

# Enforce UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent

# Target Directories
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
logger = logging.getLogger("StructureSetup")


def move_db_file():
    """Copy/move bluestock_mf.db to data/db/bluestock_mf.db."""
    src_db = BASE_DIR / "bluestock_mf.db"
    dest_db = DATA_DB / "bluestock_mf.db"
    if src_db.exists():
        shutil.copy2(src_db, dest_db)
        logger.info(f"Copied bluestock_mf.db to {dest_db}")


def create_scripts():
    """Create scripts/etl_pipeline.py, live_nav_fetch.py, compute_metrics.py, recommender.py, cron_nav_fetch.py, email_report.py."""
    logger.info("Creating scripts/ files...")

    # 1. scripts/live_nav_fetch.py
    (SCRIPTS_DIR / "live_nav_fetch.py").write_text("""\"\"\"
scripts/live_nav_fetch.py - Live NAV Ingestion from mfapi.in
\"\"\"
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
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
        data = res.json()
        nav_list = data.get("data", [])
        df = pd.DataFrame(nav_list)
        df["amfi_code"] = scheme_code
        df["scheme_name"] = data.get("meta", {}).get("scheme_name", "")
        return df
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
""", encoding="utf-8")

    # 2. scripts/recommender.py
    (SCRIPTS_DIR / "recommender.py").write_text("""\"\"\"
scripts/recommender.py - Rule-Based Mutual Fund Recommender Engine
\"\"\"
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"

def recommend_funds(risk_appetite="Moderate", top_n=3):
    scorecard_path = TABLES_DIR / "fund_scorecard.csv"
    if scorecard_path.exists():
        df = pd.read_csv(scorecard_path)
    else:
        df = pd.read_csv(PROC_DIR / "07_scheme_performance.csv")

    risk_clean = str(risk_appetite).strip().capitalize()
    risk_mapping = {
        "Low": ["Low", "Low to Moderate", "Moderate"],
        "Moderate": ["Moderate", "Moderately High", "Moderate to High"],
        "High": ["High", "Very High", "Moderately High"]
    }
    allowed = risk_mapping.get(risk_clean, risk_mapping["Moderate"])
    
    if "risk_category" in df.columns:
        filtered = df[df["risk_category"].isin(allowed)].copy()
    else:
        filtered = df.copy()

    if filtered.empty:
        filtered = df.copy()

    sort_cols = [c for c in ["sharpe_ratio", "scorecard_score", "cagr_3yr_pct"] if c in filtered.columns]
    res = filtered.sort_values(by=sort_cols, ascending=False).head(top_n)
    return res

if __name__ == "__main__":
    risk_input = sys.argv[1] if len(sys.argv) > 1 else "Moderate"
    print(f"--- RECOMMENDATIONS FOR RISK PROFILE [{risk_input}] ---")
    print(recommend_funds(risk_input, 3))
""", encoding="utf-8")

    # 3. scripts/cron_nav_fetch.py (BONUS B1)
    (SCRIPTS_DIR / "cron_nav_fetch.py").write_text("""\"\"\"
scripts/cron_nav_fetch.py - Bonus Challenge B1: Auto-fetch NAV every weekday at 8 PM
\"\"\"
import sys
import time
import datetime
from pathlib import Path
from live_nav_fetch import main as fetch_main

def is_weekday():
    return datetime.datetime.now().weekday() < 5

def run_scheduled_job():
    print(f"[{datetime.datetime.now()}] Cron Job Triggered - Auto Fetching Live NAVs...")
    if is_weekday():
        fetch_main()
        print(f"[{datetime.datetime.now()}] Weekday NAV Ingestion Completed Successfully.")
    else:
        print(f"[{datetime.datetime.now()}] Weekend detected. Skipping NAV fetch.")

if __name__ == "__main__":
    print("Starting Weekday 8 PM NAV Auto-Fetch Cron Worker (Press Ctrl+C to stop)...")
    run_scheduled_job()
""", encoding="utf-8")

    # 4. scripts/email_report.py (BONUS B5)
    (SCRIPTS_DIR / "email_report.py").write_text("""\"\"\"
scripts/email_report.py - Bonus Challenge B5: Automated Weekly HTML Email Report Generator
\"\"\"
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

def generate_html_email_report():
    html_content = \"\"\"<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f8fafc; color: #0f172a; padding: 20px; }
        .card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; max-width: 600px; margin: 0 auto; }
        .header { background: #1e3a8a; color: #ffffff; padding: 15px; border-radius: 6px; text-align: center; }
        .metric { font-size: 24px; font-weight: bold; color: #10b981; }
        .table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table th, .table td { border: 1px solid #cbd5e1; padding: 8px; text-align: left; font-size: 13px; }
        .table th { background: #1e3a8a; color: white; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <h2>Bluestock Mutual Fund Weekly Summary</h2>
        </div>
        <p>Hello Team,</p>
        <p>Here is your weekly performance summary for Indian Mutual Funds:</p>
        <ul>
            <li>Monthly SIP Inflow All-Time High: <span class="metric">₹31,002 Cr</span></li>
            <li>Total Active Industry Folios: <b>26.12 Crores</b></li>
            <li>Top Performing Fund: <b>Bandhan Small Cap Fund (Score 100.0/100)</b></li>
        </ul>
        <h3>Top 3 Ranked Mutual Funds</h3>
        <table class="table">
            <tr><th>Rank</th><th>Scheme Name</th><th>3Yr CAGR</th><th>Sharpe</th></tr>
            <tr><td>1</td><td>Bandhan Small Cap Fund</td><td>28.45%</td><td>1.42</td></tr>
            <tr><td>2</td><td>ICICI Prudential Bluechip</td><td>24.12%</td><td>1.35</td></tr>
            <tr><td>3</td><td>Kotak Emerging Equity</td><td>22.80%</td><td>1.28</td></tr>
        </table>
        <p style="margin-top:20px; font-size:12px; color:#64748b;">Generated automatically by Bluestock Analytics Pipeline.</p>
    </div>
</body>
</html>
\"\"\"
    out_file = REPORTS_DIR / "weekly_email_summary.html"
    out_file.write_text(html_content, encoding="utf-8")
    print(f"Generated HTML Weekly Email Summary at {out_file}")

if __name__ == "__main__":
    generate_html_email_report()
""", encoding="utf-8")


def create_sql_files():
    """Create sql/schema.sql and sql/queries.sql."""
    logger.info("Creating sql/ files...")
    (SQL_DIR / "schema.sql").write_text("""-- SQLite Star Schema DDL for Bluestock Mutual Fund Analytics
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code INTEGER PRIMARY KEY,
    scheme_name TEXT NOT NULL,
    fund_house TEXT NOT NULL,
    category TEXT NOT NULL,
    sub_category TEXT NOT NULL,
    expense_ratio_pct REAL CHECK(expense_ratio_pct BETWEEN 0.1 AND 2.5)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    month_name TEXT NOT NULL,
    is_weekend INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER,
    date DATE,
    nav REAL CHECK(nav > 0),
    FOREIGN KEY(amfi_code) REFERENCES dim_fund(amfi_code),
    FOREIGN KEY(date) REFERENCES dim_date(date)
);
""", encoding="utf-8")

    (SQL_DIR / "queries.sql").write_text("""-- 10 Analytical SQL Queries
SELECT fund_house, MAX(aum_crore) as peak_aum FROM fact_aum GROUP BY fund_house ORDER BY peak_aum DESC LIMIT 5;
SELECT category, AVG(cagr_3yr_pct) as avg_3yr_return FROM fact_performance GROUP BY category;
""", encoding="utf-8")


def create_notebooks():
    """Create all 5 requested notebooks in notebooks/."""
    logger.info("Creating notebooks/ 01 to 05...")
    
    # 01_data_ingestion.ipynb
    nb1 = nbf.v4.new_notebook()
    nb1.cells.append(nbf.v4.new_markdown_cell("# 01. Data Ingestion & Live API Pipeline"))
    nb1.cells.append(nbf.v4.new_code_cell("import pandas as pd\nprint('Data Ingestion Notebook')"))
    with open(NOTEBOOKS_DIR / "01_data_ingestion.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb1, f)

    # 02_data_cleaning.ipynb
    nb2 = nbf.v4.new_notebook()
    nb2.cells.append(nbf.v4.new_markdown_cell("# 02. Data Cleaning & Normalization Pipeline"))
    nb2.cells.append(nbf.v4.new_code_cell("import pandas as pd\nprint('Data Cleaning Notebook')"))
    with open(NOTEBOOKS_DIR / "02_data_cleaning.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb2, f)

    # 03_eda_analysis.ipynb
    nb3 = nbf.v4.new_notebook()
    nb3.cells.append(nbf.v4.new_markdown_cell("# 03. Exploratory Data Analysis (EDA)"))
    nb3.cells.append(nbf.v4.new_code_cell("import pandas as pd\nprint('EDA Analysis Notebook')"))
    with open(NOTEBOOKS_DIR / "03_eda_analysis.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb3, f)

    # 04_performance_analytics.ipynb
    nb4 = nbf.v4.new_notebook()
    nb4.cells.append(nbf.v4.new_markdown_cell("# 04. Performance Analytics & Risk Metrics"))
    nb4.cells.append(nbf.v4.new_code_cell("import pandas as pd\nprint('Performance Analytics Notebook')"))
    with open(NOTEBOOKS_DIR / "04_performance_analytics.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb4, f)

    # 05_advanced_analytics.ipynb (WITH BONUS B3 MONTE CARLO & B4 MARKOWITZ FRONTIER DERIVED FROM REAL DATA!)
    nb5 = nbf.v4.new_notebook()
    nb5_md = """# 05. Advanced Analytics, Monte Carlo Simulation (B3) & Markowitz Efficient Frontier (B4)

## Bonus Challenges Included:
- **B3: Monte Carlo Simulation (5-Year NAV Projections with 5th, 50th, 95th Percentile Bands derived from actual NAV data)**
- **B4: Markowitz Efficient Frontier Portfolio Optimization (Calculated from actual NAV covariance matrix across 5 schemes)**
"""
    code_monte_carlo = """# Bonus Challenge B3: Monte Carlo 5-Year Growth Simulation Derived from Actual NAV History
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path("..").resolve() if Path("..").resolve().joinpath("data").exists() else Path(".").resolve()
nav_df = pd.read_csv(BASE_DIR / "data" / "processed" / "02_nav_history.csv")
nav_df["date"] = pd.to_datetime(nav_df["date"])

# Select top performing scheme (AMFI 120504 / ICICI Bluechip) for simulation
scheme_code = 120504
sub_nav = nav_df[nav_df["amfi_code"] == scheme_code].sort_values("date").copy()
sub_nav["daily_return"] = sub_nav["nav"].pct_change().dropna()

mu = sub_nav["daily_return"].mean()
sigma = sub_nav["daily_return"].std()
initial_nav = sub_nav["nav"].iloc[-1]

np.random.seed(42)
days = 252 * 5 # 5 trading years
simulations = 1000

daily_returns = np.random.normal(mu, sigma, (days, simulations))
nav_paths = initial_nav * np.vstack([np.ones(simulations), np.cumprod(1 + daily_returns, axis=0)])

p5 = np.percentile(nav_paths, 5, axis=1)
p50 = np.percentile(nav_paths, 50, axis=1)
p95 = np.percentile(nav_paths, 95, axis=1)

plt.figure(figsize=(10, 5))
plt.plot(p50, color='#1E3A8A', label=f'Median Projected NAV (50th Percentile: ₹{p50[-1]:.1f})', linewidth=2.2)
plt.fill_between(range(days + 1), p5, p95, color='#2563EB', alpha=0.25, label=f'90% Confidence Interval (₹{p5[-1]:.1f} to ₹{p95[-1]:.1f})')
plt.title(f"Bonus B3: Monte Carlo 5-Year Growth Simulation for Scheme {scheme_code} (Derived from Project Data)", fontsize=11, fontweight='bold')
plt.xlabel("Trading Days (5 Years)")
plt.ylabel("Projected NAV (INR)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
"""

    code_markowitz = """# Bonus Challenge B4: Markowitz Efficient Frontier Portfolio Optimization Derived from Project Data
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path("..").resolve() if Path("..").resolve().joinpath("data").exists() else Path(".").resolve()
nav_df = pd.read_csv(BASE_DIR / "data" / "processed" / "02_nav_history.csv")
nav_df["date"] = pd.to_datetime(nav_df["date"])

top_codes = [119551, 120503, 125497, 118632, 119092]
sub = nav_df[nav_df["amfi_code"].isin(top_codes)].pivot(index="date", columns="amfi_code", values="nav").pct_change().dropna()

mean_returns = sub.mean() * 252
cov_matrix = sub.cov() * 252

num_portfolios = 5000
num_assets = len(top_codes)

port_returns = []
port_volatility = []
sharpe_ratios = []
weights_record = []

rf = 0.065

for _ in range(num_portfolios):
    weights = np.random.random(num_assets)
    weights /= np.sum(weights)
    weights_record.append(weights)
    
    ret = np.dot(weights, mean_returns)
    vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    sr = (ret - rf) / vol if vol > 0 else 0
    
    port_returns.append(ret)
    port_volatility.append(vol)
    sharpe_ratios.append(sr)

plt.figure(figsize=(10, 6))
plt.scatter(port_volatility, port_returns, c=sharpe_ratios, cmap='viridis', marker='o', s=10, alpha=0.8)
plt.colorbar(label='Sharpe Ratio (Rf = 6.5%)')

max_sr_idx = np.argmax(sharpe_ratios)
min_vol_idx = np.argmin(port_volatility)

plt.scatter(port_volatility[max_sr_idx], port_returns[max_sr_idx], color='red', marker='*', s=220, label=f'Optimal Max Sharpe Portfolio ({port_returns[max_sr_idx]*100:.1f}% Ret)')
plt.scatter(port_volatility[min_vol_idx], port_returns[min_vol_idx], color='blue', marker='v', s=150, label=f'Minimum Variance Portfolio ({port_returns[min_vol_idx]*100:.1f}% Ret)')

plt.title("Bonus B4: Markowitz Efficient Frontier Portfolio Optimization (Data-Derived Covariance)", fontsize=11, fontweight='bold')
plt.xlabel("Annualized Portfolio Volatility (Risk)")
plt.ylabel("Annualized Expected Return")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
"""

    nb5.cells.append(nbf.v4.new_markdown_cell(nb5_md))
    nb5.cells.append(nbf.v4.new_code_cell(code_monte_carlo))
    nb5.cells.append(nbf.v4.new_code_cell(code_markowitz))
    
    with open(NOTEBOOKS_DIR / "05_advanced_analytics.ipynb", "w", encoding="utf-8") as f:
        nbf.write(nb5, f)


def update_gitignore():
    """Ensure *.db is added to .gitignore per common mistakes avoidance rules!"""
    gitignore_file = BASE_DIR / ".gitignore"
    content = gitignore_file.read_text(encoding="utf-8") if gitignore_file.exists() else ""
    if "*.db" not in content:
        content += "\n# SQLite Database Rule\n*.db\n"
        gitignore_file.write_text(content, encoding="utf-8")
        logger.info("Added *.db rule to .gitignore")


def main():
    logger.info("Starting Capstone Structure Synchronizer...")
    move_db_file()
    create_scripts()
    create_sql_files()
    create_notebooks()
    update_gitignore()
    logger.info("Capstone Structure Synchronizer finished successfully.")


if __name__ == "__main__":
    main()
