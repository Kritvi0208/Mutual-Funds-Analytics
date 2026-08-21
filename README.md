# Bluestock Mutual Fund Analytics — Institutional Portfolio & Risk Analytics Suite

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database-SQLite3](https://img.shields.io/badge/Database-SQLite3-green.svg)](https://www.sqlite.org/)
[![Streamlit Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-red.svg)](https://streamlit.io/)

An institutional-grade empirical mutual fund analytics platform covering **64,320 daily NAV observations**, **32,778 investor transaction logs**, and **10 mutual fund master datasets**.

---

## 📑 Project Overview & Architecture

This repository delivers an end-to-end financial analytics ecosystem for Indian Mutual Funds:
- **ETL Pipeline**: Data cleaning, schema validation, and weekend/holiday NAV forward-filling (`data_cleaner.py`).
- **Star Schema Database**: Dimensional SQLite database `bluestock_mf.db` (**105,745 records** across 11 tables with 100% row parity).
- **Quantitative Risk Modeling**: 1Yr/3Yr/5Yr CAGR, Sharpe Ratio ($R_f=6.5\%$), Sortino Ratio, OLS Alpha/Beta regression against Nifty 100 benchmark, Maximum Drawdown, and 95% Historical VaR/CVaR.
- **Composite 0–100 Fund Scorecard**: 5-factor weighted rating scale evaluating return, risk, alpha, expense ratio, and tail drawdown.
- **Standalone Recommender Engine (`recommender.py`)**: Rule-based fund recommendation system matching investor risk profiles (`Low`, `Moderate`, `High`).
- **Interactive Web Dashboard (`dashboard/app.py`)**: Multi-page Streamlit dashboard with Fund Explorer, Risk Scatter Plots, Interactive SIP Wealth Calculator, and Recommender UI.

---

## 📁 Repository Directory Structure

```text
Mutual Funds Analytics/
├── data/
│   ├── raw/                   <- 10 official Bluestock CSVs + Live API NAV CSVs
│   └── processed/             <- 10 cleaned CSV datasets
├── reports/
│   ├── figures/               <- 15+ high-res PNG chart figures
│   ├── tables/                <- fund_scorecard.csv, alpha_beta.csv, var_cvar_report.csv
│   ├── Final_Report.pdf       <- 15-20 page comprehensive PDF report
│   └── Bluestock_MF_Presentation.pptx <- 12-slide PowerPoint presentation
├── notebooks/
│   ├── EDA_Analysis.ipynb     <- Pre-rendered 3.48 MB EDA notebook with 10 insights
│   ├── Performance_Analytics.ipynb <- Performance & risk analytics notebook
│   └── Advanced_Analytics.ipynb    <- VaR, CVaR, cohorts, HHI & recommender notebook
├── dashboard/
│   ├── app.py                 <- Interactive Streamlit web application
│   └── requirements_dashboard.txt
├── bluestock_mf.db            <- SQLite 3 Star Schema database (105,745 rows)
├── schema.sql                 <- Complete Star Schema DDL with PK/FK & indexes
├── queries.sql                <- 10 verified analytical SQL queries
├── data_dictionary.md         <- Technical data dictionary & schema specification
├── run_pipeline.py            <- Master pipeline execution script
├── data_ingestion.py          <- ETL data ingestion script
├── data_cleaner.py            <- Data cleaning engine script
├── data_loader.py             <- Database loader & parity verifier script
├── generate_eda.py            <- EDA chart & notebook generator script
├── generate_performance.py    <- Performance engine script
├── generate_advanced.py       <- Advanced analytics script
├── generate_presentation.py   <- Presentation deck generator script
├── generate_final_pdf.py      <- PDF report generator script
├── recommender.py             <- Standalone fund recommendation module
└── requirements.txt           <- Dependency configuration
```

---

## ⚡ Quick Start & Setup Instructions

### 1. Environment Installation
```bash
git clone https://github.com/Kritvi0208/Mutual-Funds-Analytics.git
cd "Mutual Funds Analytics"
pip install -r requirements.txt
```

### 2. Run Master Execution Pipeline
To run the complete ETL, database loading, financial analytics, figure generation, and report building from scratch:
```bash
python run_pipeline.py
```

### 3. Launch Interactive Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

---

## 🧮 Standalone Fund Recommender Engine (`recommender.py`)

You can run the fund recommender directly from the command line:

```bash
# Get Top 3 fund recommendations for Moderate risk profile
python recommender.py --risk Moderate --top 3

# Get Top 5 fund recommendations for High risk profile
python recommender.py --risk High --top 5
```

Or import as a module in Python:
```python
from recommender import recommend_funds

recs = recommend_funds(risk_appetite="Moderate", top_n=3)
print(recs)
```

---

## 📊 Summary of Core Deliverables

1. **Master Execution Pipeline**: [`run_pipeline.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/run_pipeline.py)
2. **SQLite Database**: [`bluestock_mf.db`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/bluestock_mf.db) (**105,745 rows**)
3. **Streamlit Web Application**: [`dashboard/app.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/dashboard/app.py)
4. **Final PDF Report**: [`reports/Final_Report.pdf`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/reports/Final_Report.pdf)
5. **PowerPoint Presentation**: [`reports/Bluestock_MF_Presentation.pptx`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/reports/Bluestock_MF_Presentation.pptx)
6. **Recommender Script**: [`recommender.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/recommender.py)
7. **Jupyter Notebooks**:
   - [`notebooks/EDA_Analysis.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/EDA_Analysis.ipynb)
   - [`notebooks/Performance_Analytics.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/Performance_Analytics.ipynb)
   - [`notebooks/Advanced_Analytics.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/Advanced_Analytics.ipynb)
