# Power BI Desktop Setup Guide for Bluestock Mutual Fund Analytics

This guide provides step-by-step instructions for importing the project's cleaned datasets, configuring relationships, applying DAX measures, and saving `dashboard/bluestock_mf_dashboard.pbix` in Power BI Desktop.

---

## 🛠️ Step 1: Open Power BI Desktop & Import Cleaned Data

1. Launch **Microsoft Power BI Desktop**.
2. Click **Get Data** -> Select **Folder** (or **CSV / Text**).
3. Point to your project directory: `data/processed/`
   - Select all 10 CSV files:
     - `01_fund_master.csv` (`dim_fund`)
     - `02_nav_history.csv` (`fact_nav`)
     - `03_aum_by_fund_house.csv` (`fact_aum`)
     - `04_monthly_sip_inflows.csv` (`fact_sip_inflows`)
     - `05_category_inflows.csv` (`fact_category_inflows`)
     - `06_industry_folio_count.csv` (`fact_industry_folios`)
     - `07_scheme_performance.csv` (`fact_performance`)
     - `08_investor_transactions.csv` (`fact_transactions`)
     - `09_portfolio_holdings.csv` (`fact_portfolio_holdings`)
     - `10_benchmark_indices.csv` (`fact_benchmark`)
4. Click **Load**.

---

## 🔗 Step 2: Configure Model Relationships

In the **Model View** tab, verify/create the following primary key to foreign key relationships:

1. `dim_fund[amfi_code]` (1) ───> `fact_nav[amfi_code]` (*)
2. `dim_fund[amfi_code]` (1) ───> `fact_performance[amfi_code]` (1)
3. `dim_fund[amfi_code]` (1) ───> `fact_transactions[amfi_code]` (*)
4. `dim_fund[amfi_code]` (1) ───> `fact_portfolio_holdings[amfi_code]` (*)

---

## 📐 Step 3: Apply DAX Measures

Copy and paste the measures from [`dashboard/dax_measures.dax`](file:///c:/Users/kayri/OneDrive%20-%20IIT%20BHU/Documents/Mutual%20Funds%20Analytics/dashboard/dax_measures.dax):

```dax
Total AUM (Cr) = SUM(fact_aum[aum_crore])

Monthly SIP Inflow (Cr) = MAX(fact_sip_inflows[sip_inflow_crore])

Total Folios (Cr) = MAX(fact_industry_folios[total_folios_crore])

Total Schemes = DISTINCTCOUNT(dim_fund[amfi_code])

Average 3Yr CAGR (%) = AVERAGE(fact_performance[cagr_3yr_pct])

Average Sharpe Ratio = AVERAGE(fact_performance[sharpe_ratio])

FY25 Net Inflow (Cr) = 
CALCULATE(
    SUM(fact_category_inflows[net_inflow_crore]),
    FILTER(
        fact_category_inflows,
        fact_category_inflows[month] >= DATE(2024, 4, 1) && 
        fact_category_inflows[month] <= DATE(2025, 3, 31)
    )
)
```

---

## 📊 Step 4: Build Dashboard Pages & Save .pbix

1. **Page 1 (Industry Overview)**: KPI cards for AUM, SIP, Folios, Schemes + Industry AUM Trend line + AUM by AMC bar chart.
2. **Page 2 (Fund Performance)**: Scatter plot (Return vs Risk, size = AUM) + Sortable Scorecard table + Scheme NAV vs Benchmark.
3. **Page 3 (Investor Analytics)**: Transaction amount by state horizontal bar + Donut split (SIP/Lumpsum/Redemption) + Age group vs Avg SIP bar.
4. **Page 4 (SIP & Market Trends)**: Dual-axis SIP inflow bar + Nifty 50 line + Category inflow heatmap + Top 5 FY25 net inflow categories.
5. Click **File -> Save As** -> Save to `dashboard/bluestock_mf_dashboard.pbix`.
