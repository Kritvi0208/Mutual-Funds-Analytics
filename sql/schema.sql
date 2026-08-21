-- ====================================================================
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
