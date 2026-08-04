-- Bluestock Mutual Fund Analytics - 10 Analytical SQL Queries
-- Target Database: bluestock_mf.db

-- QUERY 1: Top 5 Funds by AUM (Assets Under Management in Crores)
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    p.aum_crore,
    p.return_3yr_pct
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- QUERY 2: Average NAV per Month per Scheme (Monthly NAV Trends)
SELECT 
    f.amfi_code,
    f.scheme_name,
    strftime('%Y-%m', n.date) AS month,
    ROUND(AVG(n.nav), 2) AS avg_monthly_nav,
    ROUND(MIN(n.nav), 2) AS min_monthly_nav,
    ROUND(MAX(n.nav), 2) AS max_monthly_nav
FROM fact_nav n
JOIN dim_fund f ON n.amfi_code = f.amfi_code
GROUP BY f.amfi_code, strftime('%Y-%m', n.date)
ORDER BY f.amfi_code, month DESC;

-- QUERY 3: Monthly SIP Inflows & YoY Growth Trends
SELECT 
    month,
    sip_inflow_crore,
    active_sip_accounts_crore,
    new_sip_accounts_lakh,
    sip_aum_lakh_crore,
    COALESCE(yoy_growth_pct, 0.0) AS yoy_growth_pct
FROM fact_sip_inflows
ORDER BY month DESC;

-- QUERY 4: Investor Transactions and Total Amount by State
SELECT 
    state,
    COUNT(transaction_id) AS total_transactions,
    COUNT(DISTINCT investor_id) AS unique_investors,
    ROUND(SUM(amount_inr), 2) AS total_investment_inr,
    ROUND(AVG(amount_inr), 2) AS avg_transaction_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_investment_inr DESC;

-- QUERY 5: Low-Cost Mutual Funds (Expense Ratio < 1.0%)
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    f.sub_category,
    f.expense_ratio_pct,
    p.return_3yr_pct,
    p.sharpe_ratio
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;

-- QUERY 6: Top 5 Risk-Adjusted Performers by 3-Year Sharpe Ratio
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    p.sharpe_ratio,
    p.sortino_ratio,
    p.alpha,
    p.return_3yr_pct
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 5;

-- QUERY 7: Sector Allocation Breakdown Across All Equity Portfolio Holdings
SELECT 
    sector,
    COUNT(DISTINCT stock_symbol) AS total_stocks,
    COUNT(DISTINCT amfi_code) AS schemes_holding,
    ROUND(AVG(weight_pct), 2) AS avg_weight_pct,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM fact_portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC;

-- QUERY 8: Net Category Inflows Over Time
SELECT 
    month,
    category,
    ROUND(SUM(net_inflow_crore), 2) AS total_net_inflow_cr
FROM fact_category_inflows
GROUP BY month, category
ORDER BY month DESC, total_net_inflow_cr DESC;

-- QUERY 9: Investor KYC Status Distribution & Transaction Volume Analysis
SELECT 
    kyc_status,
    COUNT(transaction_id) AS transaction_count,
    COUNT(DISTINCT investor_id) AS unique_investors,
    ROUND(SUM(amount_inr), 2) AS total_volume_inr,
    ROUND(AVG(amount_inr), 2) AS avg_ticket_size_inr
FROM fact_transactions
GROUP BY kyc_status
ORDER BY transaction_count DESC;

-- QUERY 10: Outperforming Alpha Generators (3Yr Return > Benchmark & Positive Alpha)
SELECT 
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    p.return_3yr_pct,
    p.benchmark_3yr_pct,
    ROUND(p.return_3yr_pct - p.benchmark_3yr_pct, 2) AS excess_return_pct,
    p.alpha,
    p.beta
FROM dim_fund f
JOIN fact_performance p ON f.amfi_code = p.amfi_code
WHERE p.return_3yr_pct > p.benchmark_3yr_pct 
  AND p.alpha > 0
ORDER BY excess_return_pct DESC;
