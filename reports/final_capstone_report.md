# Bluestock Mutual Fund Analytics — Comprehensive Final Capstone Report

**Author**: Ritvika Kulshreshtha  
**Date**: August 2026  
**Repository**: [`Kritvi0208/Mutual-Funds-Analytics`](https://github.com/Kritvi0208/Mutual-Funds-Analytics)  
**Database**: SQLite Star Schema `bluestock_mf.db` (**105,745 rows**)  

---

## 1. Executive Summary

This capstone project delivers an end-to-end institutional financial analytics platform for the Indian Mutual Fund industry. Integrating **64,320 daily NAV observations**, **32,778 investor transaction logs**, and **10 mutual fund master datasets**, the project establishes automated data pipelines, a dimensional Star Schema database, exploratory visual analytics, financial risk modeling (CAGR, Sharpe, Sortino, OLS Alpha/Beta, 95% VaR/CVaR), a 0–100 Composite Fund Scorecard, and an interactive Streamlit web application.

---

## 2. Project Lifecycle & Architecture

```
[ Raw CSV Datasets ] ──> [ ETL & Data Cleaner (data_cleaner.py) ] ──> [ Processed CSVs (data/processed/) ]
                                                                               │
                                                                               ▼
[ Streamlit Web App (app.py) ] <── [ Analytical SQL Queries ] <── [ SQLite Star Schema DB (bluestock_mf.db) ]
```

### Key Milestones Achieved:
1. **Day 1 — Production ETL & Live API**: Ingested live NAV data from `mfapi.in` for target schemes (**20,026 records**) and built production ETL pipeline with schema validation and memory optimization.
2. **Day 2 — Star Schema Database Design**: Constructed SQLite database `bluestock_mf.db` with 2 dimension tables (`dim_fund`, `dim_date`) and 7 fact tables. Verified **100% row count parity** across all 11 tables.
3. **Day 3 — Exploratory Data Analysis**: Pre-rendered [`notebooks/EDA_Analysis.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/EDA_Analysis.ipynb) with 15 publication-quality chart figures highlighting market trends.
4. **Day 4 — Fund Performance Analytics**: Executed financial risk-return modeling (Sharpe, Sortino, OLS Alpha/Beta regression) and established the **Composite 0–100 Fund Scorecard**.
5. **Day 5 — Advanced Risk & Recommender Engine**: Modeled Historical 95% VaR/CVaR, rolling 90-day Sharpe ratios, investor cohort retention, portfolio sector HHI concentration, and standalone recommender engine ([`recommender.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/recommender.py)).
6. **Day 6 — Interactive Web Application**: Developed Streamlit multi-page web app [`dashboard/app.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/dashboard/app.py).

---

## 3. Top 10 Mutual Funds Performance Scorecard (0–100 Rating Scale)

*Source: [`reports/tables/fund_scorecard.csv`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/reports/tables/fund_scorecard.csv)*

| Rank | AMFI Code | Scheme Name | Fund House | Score (0-100) | 3-Yr CAGR | Sharpe Ratio | Sortino Ratio | Alpha | Beta | Expense Ratio | Max Drawdown |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | 148567 | Bandhan Small Cap Fund - Direct Plan | Bandhan AMC | **100.00** | 28.45% | 1.42 | 2.15 | +8.24% | 0.98 | 0.45% | -11.27% |
| **2** | 120505 | ICICI Prudential Bluechip Fund - Direct | ICICI Prudential | **96.82** | 24.12% | 1.35 | 1.98 | +6.15% | 0.94 | 0.92% | -18.19% |
| **3** | 120843 | Kotak Emerging Equity Fund - Direct | Kotak Mahindra | **94.15** | 22.80% | 1.28 | 1.89 | +5.42% | 0.91 | 0.58% | -12.97% |
| **4** | 100033 | SBI Large & Midcap Fund - Direct Plan | SBI Mutual Fund | **91.48** | 21.65% | 1.22 | 1.81 | +4.88% | 0.96 | 0.78% | -16.22% |
| **5** | 120504 | ICICI Prudential Focused Equity Fund | ICICI Prudential | **88.92** | 20.95% | 1.18 | 1.74 | +4.35% | 0.93 | 0.85% | -12.59% |
| **6** | 119551 | SBI Bluechip Fund - Direct Plan | SBI Mutual Fund | **86.30** | 19.82% | 1.14 | 1.68 | +3.92% | 0.95 | 0.95% | -15.44% |
| **7** | 118632 | Nippon India Large Cap Fund - Direct | Nippon India | **83.65** | 19.10% | 1.10 | 1.62 | +3.48% | 0.97 | 0.88% | -14.82% |
| **8** | 119092 | Axis Bluechip Fund - Direct Plan | Axis AMC | **81.02** | 18.45% | 1.05 | 1.55 | +2.95% | 0.92 | 0.72% | -13.91% |
| **9** | 120841 | Kotak Bluechip Fund - Direct Plan | Kotak Mahindra | **78.41** | 17.90% | 1.01 | 1.48 | +2.50% | 0.94 | 0.81% | -14.20% |
| **10** | 125497 | HDFC Top 100 Fund - Direct Plan | HDFC AMC | **75.80** | 17.25% | 0.98 | 1.42 | +2.10% | 0.96 | 1.05% | -16.10% |

---

## 4. Key Business Findings & Strategic Recommendations

1. **SIP Capital Momentum**: Monthly SIP inflows reached an all-time high of **₹31,002 Crores in Dec 2025**, representing 134% growth over 4 years. AMCs should expand digital mandate onboarding to capture Tier 2 & Tier 3 city growth.
2. **Downside Risk Management**: Small Cap schemes exhibit higher daily tail risk (VaR 95% = -2.45%), but maintain superior Sortino ratios (2.15), proving that downside volatility is well-compensated by upside performance over 3+ year investment horizons.
3. **Low-Cost Advantage**: Schemes with expense ratios below 0.80% achieved an average +2.4% higher net CAGR over 5-year periods compared to high-expense peers (>1.50%).

---

## 5. Deliverable Directory & File Map

- **Database**: [`bluestock_mf.db`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/bluestock_mf.db)
- **Web Application**: [`dashboard/app.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/dashboard/app.py)
- **Recommender Module**: [`recommender.py`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/recommender.py)
- **Jupyter Notebooks**:
  - [`notebooks/EDA_Analysis.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/EDA_Analysis.ipynb)
  - [`notebooks/Performance_Analytics.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/Performance_Analytics.ipynb)
  - [`notebooks/Advanced_Analytics.ipynb`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/notebooks/Advanced_Analytics.ipynb)
- **Data Dictionary**: [`data_dictionary.md`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/data_dictionary.md)
- **Tabular CSV Reports**: `reports/tables/fund_scorecard.csv`, `reports/tables/alpha_beta.csv`, `reports/tables/var_cvar_report.csv`.
- **Chart Figures**: 15+ exported PNG chart files in `reports/figures/`.
