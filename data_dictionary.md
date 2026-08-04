# Bluestock Mutual Fund Analytics - Data Dictionary & Database Architecture

## 1. Executive Summary & Star Schema Architecture

The **Bluestock Mutual Fund Analytics Database** (`bluestock_mf.db`) is structured as a dimensional Star Schema designed for high-performance financial analytics, risk modeling, and investor behavior profiling. 

- **Database Engine**: SQLite 3 / SQLAlchemy
- **Data Model**: Star Schema (4 Dimensions, 7 Fact Tables)
- **Source Data**: 10 Cleaned Bluestock Capstone Datasets (`data/processed/`)
- **Total Database Records**: **105,745 rows** across 11 tables

---

## 2. Entity Relationship & Table Summary

| Table Name | Entity Type | Primary Key | Foreign Keys | Row Count | Source CSV Reference |
|---|---|---|---|---|---|
| `dim_fund` | Dimension | `amfi_code` | None | 40 | `01_fund_master.csv` |
| `dim_date` | Dimension | `date` | None | 2,706 | Generated Calendar Dimension |
| `fact_nav` | Fact Table | `nav_id` | `amfi_code`, `date` | 64,320 | `02_nav_history.csv` |
| `fact_transactions` | Fact Table | `transaction_id` | `amfi_code`, `transaction_date` | 32,778 | `08_investor_transactions.csv` |
| `fact_performance` | Fact Table | `amfi_code` | `amfi_code` | 40 | `07_scheme_performance.csv` |
| `fact_aum` | Fact Table | `aum_id` | `date` | 90 | `03_aum_by_fund_house.csv` |
| `fact_portfolio_holdings` | Fact Table | `holding_id` | `amfi_code`, `portfolio_date` | 322 | `09_portfolio_holdings.csv` |
| `fact_benchmark` | Fact Table | `benchmark_id` | `date` | 8,050 | `10_benchmark_indices.csv` |
| `fact_sip_inflows` | Fact Table | `month` | None | 48 | `04_monthly_sip_inflows.csv` |
| `fact_category_inflows` | Fact Table | `inflow_id` | None | 144 | `05_category_inflows.csv` |
| `fact_industry_folios` | Fact Table | `month` | None | 21 | `06_industry_folio_count.csv` |

---

## 3. Comprehensive Data Dictionary

### 3.1 `dim_fund` (Mutual Fund Master Dimension)
*Source: `data/processed/01_fund_master.csv`*

| Column Name | SQLite Data Type | Key Type | Constraint | Business Definition & Validation Rules |
|---|---|---|---|---|
| `amfi_code` | `INTEGER` | **PK** | NOT NULL, UNIQUE | 6-digit unique AMFI scheme code identifying the mutual fund variant. |
| `scheme_name` | `TEXT` | - | NOT NULL | Complete official mutual fund scheme name. |
| `fund_house` | `TEXT` | - | NOT NULL | Asset Management Company (AMC) managing the fund. |
| `category` | `TEXT` | - | NOT NULL | Broad asset class category (Equity, Debt). |
| `sub_category` | `TEXT` | - | NOT NULL | SEBI sub-category classification (Large Cap, Mid Cap, ELSS, Liquid, etc.). |
| `plan` | `TEXT` | - | - | Plan type (Direct Plan - Growth). |
| `launch_date` | `DATE` | - | - | Fund inception/launch date (YYYY-MM-DD). |
| `benchmark` | `TEXT` | - | - | Target benchmark index (e.g. NIFTY 100 TRI, S&P BSE SENSEX TRI). |
| `expense_ratio_pct` | `REAL` | - | CHECK(0.1-2.5) | Annual fund management fee percentage. |
| `exit_load_pct` | `REAL` | - | - | Percentage fee charged on early redemptions. |
| `min_sip_amount` | `REAL` | - | - | Minimum monthly SIP investment amount (INR). |
| `min_lumpsum_amount` | `REAL` | - | - | Minimum initial lumpsum purchase amount (INR). |
| `fund_manager` | `TEXT` | - | - | Name of primary portfolio fund manager. |
| `risk_category` | `TEXT` | - | - | SEBI Riskometer rating (Low, Moderate, High, Very High). |
| `sebi_category_code` | `INTEGER` | - | - | Numeric SEBI category classification code. |

---

### 3.2 `dim_date` (Calendar Dimension)
*Source: Generated Calendar Range (2020-01-01 to 2027-07-24)*

| Column Name | SQLite Data Type | Key Type | Constraint | Business Definition & Validation Rules |
|---|---|---|---|---|
| `date` | `DATE` | **PK** | NOT NULL, UNIQUE | Calendar date string formatted as `YYYY-MM-DD`. |
| `year` | `INTEGER` | - | NOT NULL | 4-digit calendar year (e.g. 2024). |
| `quarter` | `INTEGER` | - | 1 to 4 | Calendar quarter number (1, 2, 3, 4). |
| `month` | `INTEGER` | - | 1 to 12 | Calendar month number (1 to 12). |
| `month_name` | `TEXT` | - | NOT NULL | Full month name (January, February, etc.). |
| `day` | `INTEGER` | - | 1 to 31 | Day of the month. |
| `day_name` | `TEXT` | - | NOT NULL | Full day name (Monday, Tuesday, etc.). |
| `day_of_week` | `INTEGER` | - | 1 to 7 | Day of week index (1 = Monday, 7 = Sunday). |
| `is_weekend` | `INTEGER` | - | 0 or 1 | Flag indicating weekend (1 = Saturday/Sunday, 0 = Weekday). |

---

### 3.3 `fact_nav` (Daily Net Asset Value Fact Table)
*Source: `data/processed/02_nav_history.csv`*

| Column Name | SQLite Data Type | Key Type | Constraint | Business Definition & Validation Rules |
|---|---|---|---|---|
| `nav_id` | `INTEGER` | **PK** | AUTOINCREMENT | Surrogate primary key for NAV entry. |
| `amfi_code` | `INTEGER` | **FK** | `dim_fund(amfi_code)` | References AMFI scheme code. |
| `date` | `DATE` | **FK** | `dim_date(date)` | Reference valuation date. |
| `nav` | `REAL` | - | CHECK(nav > 0) | Per-unit Net Asset Value in INR. Forward-filled for non-trading weekend/holiday dates. |

---

### 3.4 `fact_transactions` (Investor Transaction Logs)
*Source: `data/processed/08_investor_transactions.csv`*

| Column Name | SQLite Data Type | Key Type | Constraint | Business Definition & Validation Rules |
|---|---|---|---|---|
| `transaction_id` | `TEXT` | **PK** | NOT NULL, UNIQUE | Unique transaction identifier (e.g. TXN003054). |
| `investor_id` | `TEXT` | - | NOT NULL | Unique investor customer identifier. |
| `transaction_date` | `DATE` | **FK** | `dim_date(date)` | Transaction execution date. |
| `amfi_code` | `INTEGER` | **FK** | `dim_fund(amfi_code)` | Target mutual fund scheme AMFI code. |
| `transaction_type` | `TEXT` | - | CHECK(enum) | Standardised transaction type: `SIP`, `Lumpsum`, `Redemption`, `STP`, `SWP`. |
| `amount_inr` | `REAL` | - | CHECK(amount > 0) | Transaction value in Indian Rupees (INR). |
| `state` | `TEXT` | - | - | Investor home state in India. |
| `city` | `TEXT` | - | - | Investor city location. |
| `city_tier` | `TEXT` | - | - | Tier classification (Tier 1, Tier 2, Tier 3). |
| `age_group` | `TEXT` | - | - | Demographics age bracket (18-25, 26-35, 36-50, 50+). |
| `gender` | `TEXT` | - | - | Investor gender identity. |
| `annual_income_lakh` | `REAL` | - | - | Self-reported annual income in INR Lakhs. |
| `payment_mode` | `TEXT` | - | - | Payment mode used (UPI, NetBanking, Mandate, Cheque). |
| `kyc_status` | `TEXT` | - | CHECK(enum) | Investor KYC compliance status: `Verified`, `Pending`, `Rejected`. |

---

### 3.5 `fact_performance` (Scheme Performance & Risk Analytics)
*Source: `data/processed/07_scheme_performance.csv`*

| Column Name | SQLite Data Type | Key Type | Constraint | Business Definition & Validation Rules |
|---|---|---|---|---|
| `amfi_code` | `INTEGER` | **PK, FK** | `dim_fund(amfi_code)` | Target mutual fund scheme code. |
| `return_1yr_pct` | `REAL` | - | - | 1-Year annualized return percentage. |
| `return_3yr_pct` | `REAL` | - | - | 3-Year CAGR return percentage. |
| `return_5yr_pct` | `REAL` | - | - | 5-Year CAGR return percentage. |
| `benchmark_3yr_pct` | `REAL` | - | - | Benchmark index 3-year return percentage. |
| `alpha` | `REAL` | - | - | Excess risk-adjusted return over benchmark (Jensen's Alpha). |
| `beta` | `REAL` | - | - | Systematic market risk exposure relative to benchmark. |
| `sharpe_ratio` | `REAL` | - | - | Risk-adjusted return metric (Excess return per unit total risk). |
| `sortino_ratio` | `REAL` | - | - | Risk-adjusted return metric focusing on downside volatility. |
| `std_dev_ann_pct` | `REAL` | - | - | Annualized standard deviation of returns (volatility). |
| `max_drawdown_pct` | `REAL` | - | <= 0 | Maximum peak-to-trough percentage decline experienced. |
| `aum_crore` | `REAL` | - | > 0 | Total Assets Under Management in INR Crores. |
| `expense_ratio_pct` | `REAL` | - | CHECK(0.1-2.5) | Annual operating expense ratio. |
| `morningstar_rating` | `INTEGER` | - | 1 to 5 | Morningstar star rating. |
| `risk_grade` | `TEXT` | - | - | Quantitative risk category rating. |

---

### 3.6 `fact_portfolio_holdings` (Stock Holding Distribution)
*Source: `data/processed/09_portfolio_holdings.csv`*

| Column Name | SQLite Data Type | Key Type | Constraint | Business Definition & Validation Rules |
|---|---|---|---|---|
| `holding_id` | `INTEGER` | **PK** | AUTOINCREMENT | Primary key for holding record. |
| `amfi_code` | `INTEGER` | **FK** | `dim_fund(amfi_code)` | Holding mutual fund scheme code. |
| `stock_symbol` | `TEXT` | - | NOT NULL | NSE/BSE stock ticker symbol (e.g. HDFCBANK, RELIANCE). |
| `stock_name` | `TEXT` | - | - | Official company name. |
| `sector` | `TEXT` | - | - | Industry sector classification (Financial Services, IT, Energy, etc.). |
| `weight_pct` | `REAL` | - | 0 to 100 | Percentage weight of stock in total fund portfolio. |
| `market_value_cr` | `REAL` | - | - | Market value of holding in INR Crores. |
| `current_price_inr` | `REAL` | - | - | Stock unit market price in INR. |
| `portfolio_date` | `DATE` | **FK** | `dim_date(date)` | Holding report date. |

---

## 4. Data Cleaning Audit & Transformation Rules

1. **NAV History Forward-Filling**:
   - Converted dates to `datetime64[ns]`.
   - Filtered out non-positive NAV values (`nav > 0`).
   - Deduplicated on `(amfi_code, date)`.
   - Reindexed each scheme onto a complete daily date range and applied `.ffill().bfill()` to simulate weekend/holiday NAV continuity.

2. **Transaction Enums & Validation**:
   - Standardised `transaction_type` strings into canonical uppercase values (`SIP`, `Lumpsum`, `Redemption`, `STP`, `SWP`).
   - Validated positive transaction amounts (`amount_inr > 0`).
   - Mapped non-standard KYC status strings to canonical enum (`Verified`, `Pending`, `Rejected`).

3. **Performance Metrics Range Checks**:
   - Verified expense ratios fall within standard regulatory limits (0.1% to 2.5%).
   - Preserved negative representation for `max_drawdown_pct`.

4. **Database Row Count Parity Verification**:
   - Verified 100% row count parity between all 10 source CSVs in `data/processed/` and the SQLite database `bluestock_mf.db`.
