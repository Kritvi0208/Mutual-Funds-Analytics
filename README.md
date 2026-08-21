# Bluestock Mutual Fund Analytics — Institutional Portfolio & Risk Analytics Platform

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database-SQLite3](https://img.shields.io/badge/Database-SQLite3-green.svg)](https://www.sqlite.org/)
[![Streamlit Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)
[![Power BI](https://img.shields.io/badge/Dashboard-Power%20BI-yellow.svg)](https://powerbi.microsoft.com/)

An institutional-grade empirical mutual fund analytics and data engineering platform covering **64,320 daily NAV observations**, **32,778 investor transaction logs**, and **10 relational mutual fund master datasets**.

---

## 📑 Project Overview & Architecture

This repository delivers an end-to-end financial analytics ecosystem for Indian Mutual Funds:
- **ETL Data Pipeline**: Automated ingestion, schema validation, transaction normalization, and weekend/holiday NAV forward-filling (`scripts/etl_pipeline.py`).
- **Star Schema Database**: Relational SQLite database with primary keys, foreign keys, and indexes (**105,745 records** across 10 tables with 100% row parity).
- **Quantitative Risk Modeling**: 1Yr/3Yr CAGR, Sharpe Ratio ($R_f=6.5\%$), Sortino Ratio, OLS Alpha/Beta regression against Nifty 100 benchmark, Maximum Drawdown, and 95% Historical VaR/CVaR.
- **Composite 0–100 Fund Scorecard**: 5-factor weighted rating model evaluating return, risk, alpha, expense ratio, and downside resilience.
- **Investor Cohort & Continuity Analysis**: Retention modeling across 2024/2025 cohorts and SIP continuity gap analysis (identifying at-risk investors with gaps >35 days).
- **Interactive Dashboards**: 
  - **Streamlit Web Application (`dashboard/app.py`)**: 5 interactive views in Light Pastel UI (Executive Overview, Scorecard Explorer, Risk-Return Analytics, SIP Calculator, and Recommender).
  - **Power BI Dashboard (`dashboard/bluestock_mf_dashboard.pbix`)**: 4-page interactive visual analytics dashboard with DAX measures.
- **Automated Reporting**: 15-page comprehensive capstone PDF report, 12-slide executive presentation deck, and automated weekly HTML email briefs.

---

## 📁 Repository Directory Structure

```text
Mutual-Funds-Analytics/
├── data/
│   ├── raw/                           # 10 official raw CSVs + Live API NAV CSVs
│   ├── processed/                     # 10 cleaned & normalized CSV datasets
│   └── db/                            # SQLite database directory (ignored by git)
├── notebooks/
│   ├── 01_data_ingestion.ipynb        # Data ingestion & live API fetch pipeline
│   ├── 02_data_cleaning.ipynb         # Data cleaning, validation & normalization
│   ├── 03_eda_analysis.ipynb          # Exploratory Data Analysis (15+ charts & insights)
│   ├── 04_performance_analytics.ipynb # Performance metrics, CAGR & composite scorecards
│   └── 05_advanced_analytics.ipynb    # VaR/CVaR, Monte Carlo (1,000 paths) & Markowitz
├── scripts/
│   ├── etl_pipeline.py                # Master ETL pipeline & database loader
│   ├── compute_metrics.py             # Performance & risk calculation engine
│   ├── recommender.py                 # Rule-based fund recommendation algorithm
│   ├── live_nav_fetch.py              # Live AMFI API data ingestion (mfapi.in)
│   ├── cron_nav_fetch.py              # Weekday 8 PM automated NAV cron worker
│   ├── email_report.py                # Weekly HTML email summary generator & SMTP sender
│   ├── generate_eda.py                # 15+ EDA chart figures & notebook generator
│   ├── generate_advanced.py           # Downside risk, cohort & sector HHI engine
│   ├── generate_powerbi_dashboard.py  # Power BI dashboard renderer & PDF exporter
│   ├── generate_presentation.py       # 12-slide PowerPoint presentation generator
│   └── generate_final_pdf.py          # 15-page comprehensive capstone PDF report generator
├── sql/
│   ├── schema.sql                     # Full Star Schema DDL with PKs, FKs & indexes
│   └── queries.sql                    # 10 verified analytical SQL queries
├── dashboard/
│   ├── bluestock_mf_dashboard.pbix    # Power BI Desktop interactive dashboard
│   ├── app.py                         # Streamlit interactive web dashboard
│   ├── dax_measures.dax               # Power BI DAX measures reference
│   └── requirements_dashboard.txt     # Dashboard specific dependencies
├── reports/
│   ├── Final_Report.pdf               # 15-page comprehensive capstone project report
│   ├── Bluestock_MF_Presentation.pptx # 12-slide executive presentation deck
│   ├── Dashboard.pdf                  # 4-page compiled dashboard visual report
│   ├── weekly_email_summary.html      # Weekly email brief template
│   ├── figures/                       # 15+ publication-quality PNG charts & dashboard pages
│   └── tables/                        # Scorecards, Alpha/Beta & VaR/CVaR CSV exports
├── .gitignore                         # Excludes .db binaries, bytecode & caches
├── POWERBI_SETUP.md                   # Power BI import & DAX setup guide
├── data_dictionary.md                 # Schema & data field technical dictionary
├── requirements.txt                   # Project dependency configuration
├── README.md                          # Main project documentation
└── run_pipeline.py                    # Master single-command pipeline execution script
```

---

## ⚡ Quick Start & Setup Instructions

### 1. Environment Installation
```bash
git clone https://github.com/Kritvi0208/Mutual-Funds-Analytics.git
cd "Mutual-Funds-Analytics"
pip install -r requirements.txt
```

### 2. Run Master Execution Pipeline
To run the complete data pipeline end-to-end (ingestion, cleaning, database population, financial metric computation, figure generation, and report compilation):
```bash
python run_pipeline.py
```

### 3. Launch Interactive Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

---

## 🧮 Standalone Fund Recommender CLI (`scripts/recommender.py`)

You can run the fund recommender algorithm directly from the command line:

```bash
# Get Top 3 recommendations for Moderate risk profile
python scripts/recommender.py Moderate 3

# Get Top 5 recommendations for High risk profile
python scripts/recommender.py High 5

# Get Top 3 recommendations for Low risk profile
python scripts/recommender.py Low 3
```

Or import as a module in Python:
```python
from scripts.recommender import recommend_funds

# Generate recommendations based on investor risk appetite
recommended_df = recommend_funds(risk_appetite="Moderate", top_n=3)
print(recommended_df[["fund_rank", "scheme_name", "cagr_3yr_pct", "sharpe_ratio", "scorecard_score"]])
```

---

## 📊 Summary of Core Deliverables

| Deliverable ID | Deliverable Name | File Location | Key Metrics / Scope |
|---|---|---|---|
| **D1** | Master ETL Pipeline | [`scripts/etl_pipeline.py`](scripts/etl_pipeline.py) | Ingests 10 raw datasets, forward-fills weekend NAVs, normalizes transactions |
| **D2** | SQLite Database & SQL | [`sql/schema.sql`](sql/schema.sql), [`sql/queries.sql`](sql/queries.sql) | 105,745 rows in Star Schema DB + 10 executed analytical queries |
| **D3** | Exploratory Data Analysis | [`notebooks/03_eda_analysis.ipynb`](notebooks/03_eda_analysis.ipynb) | 15+ publication-quality charts in `reports/figures/` + 10 documented insights |
| **D4** | Fund Performance Analytics | [`scripts/compute_metrics.py`](scripts/compute_metrics.py) | 1Yr/3Yr CAGRs, Sharpe ($R_f=6.5\%$), Sortino, Alpha, Beta, Max Drawdown & 0–100 Scorecard |
| **D5** | Interactive Dashboards | [`dashboard/bluestock_mf_dashboard.pbix`](dashboard/bluestock_mf_dashboard.pbix), [`dashboard/app.py`](dashboard/app.py) | 4-page Power BI dashboard + 5-view Streamlit web app in Light Pastel theme |
| **D6** | Advanced Risk Analytics | [`notebooks/05_advanced_analytics.ipynb`](notebooks/05_advanced_analytics.ipynb) | 95% Historical VaR (-1.82%), CVaR (-2.45%), Cohorts (2024/2025), SIP Gap Continuity |
| **D7** | Capstone Report & Deck | [`reports/Final_Report.pdf`](reports/Final_Report.pdf), [`reports/Bluestock_MF_Presentation.pptx`](reports/Bluestock_MF_Presentation.pptx) | 15-page comprehensive final PDF report + 12-slide PowerPoint presentation |
| **B1–B5** | Bonus Challenges | `scripts/cron_nav_fetch.py`, `scripts/email_report.py` | 8 PM NAV fetcher, Streamlit app, Monte Carlo (1,000 paths), Markowitz & HTML email briefs |

---

## 📈 Key Analytical Insights

1. **Industry Growth**: Total Industry AUM peaked at **₹81.4 Lakh Crores** with monthly SIP inflows reaching an all-time high of **₹31,002 Crores** (Dec 2025). Total industry folios doubled from **13.26 Cr to 26.12 Cr**.
2. **Risk-Adjusted Alpha**: Top-performing large-cap and small-cap equity schemes generated annualized Alphas of **+26% to +29%** relative to the Nifty 100 benchmark.
3. **Downside Risk Benchmarks**: The average 95% Historical Daily VaR across the 40 analyzed schemes was **-1.82%**, with a Conditional VaR (CVaR) tail loss expectation of **-2.45%**.
4. **SIP Continuity & Attrition**: Analysis of 1,362 repeat investors (6+ SIP transactions) revealed that **97.8% experienced gap intervals >35 days**, underscoring the necessity of automated SIP payment continuity nudges.
