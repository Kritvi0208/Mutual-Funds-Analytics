-- 10 Analytical SQL Queries
SELECT fund_house, MAX(aum_crore) as peak_aum FROM fact_aum GROUP BY fund_house ORDER BY peak_aum DESC LIMIT 5;
SELECT category, AVG(cagr_3yr_pct) as avg_3yr_return FROM fact_performance GROUP BY category;
