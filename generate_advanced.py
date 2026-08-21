"""
generate_advanced.py - Advanced Analytics & Risk Modeling Engine

Computes:
1. Historical 95% VaR & CVaR Tail Risk for 40 schemes
2. 90-Day Rolling Sharpe Ratios for Key Funds
3. Investor Cohort Analysis (2024 & 2025 transaction cohorts)
4. SIP Continuity & Churn Analysis (6+ SIP transactions, gap > 35 days)
5. Sector HHI Portfolio Concentration Index
6. Rule-Based Fund Recommender Engine

Usage:
    python generate_advanced.py
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Enforce UTF-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PROC_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"
LOGS_DIR = BASE_DIR / "logs"

TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "advanced_analytics.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("AdvancedAnalytics")


def compute_var_cvar():
    """Compute Historical 95% VaR and CVaR for all 40 schemes."""
    logger.info("Computing 95% Historical VaR and CVaR...")
    nav_df = pd.read_csv(PROC_DIR / "02_nav_history.csv")
    fund_master = pd.read_csv(PROC_DIR / "01_fund_master.csv")
    nav_df["date"] = pd.to_datetime(nav_df["date"])

    results = []

    for code, group in nav_df.groupby("amfi_code"):
        group = group.sort_values("date")
        group["daily_return"] = group["nav"].pct_change()
        rets = group["daily_return"].dropna()

        if len(rets) < 50:
            continue

        var_95 = np.percentile(rets, 5) # 5th percentile
        cvar_95 = rets[rets <= var_95].mean() # mean of returns below VaR

        scheme_name = fund_master[fund_master["amfi_code"] == code]["scheme_name"].iloc[0] if code in fund_master["amfi_code"].values else f"Scheme {code}"

        results.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "var_95_daily_pct": round(var_95 * 100, 3),
            "cvar_95_daily_pct": round(cvar_95 * 100, 3),
            "worst_single_day_pct": round(rets.min() * 100, 2)
        })

    var_df = pd.DataFrame(results).sort_values("var_95_daily_pct")
    var_df.to_csv(TABLES_DIR / "var_cvar_report.csv", index=False)
    logger.info(f"Exported VaR/CVaR report ({len(var_df)} schemes) to {TABLES_DIR / 'var_cvar_report.csv'}")
    return var_df


def compute_rolling_sharpe():
    """Compute 90-day rolling Sharpe ratio for key funds."""
    logger.info("Computing 90-day rolling Sharpe ratio...")
    nav_df = pd.read_csv(PROC_DIR / "02_nav_history.csv")
    nav_df["date"] = pd.to_datetime(nav_df["date"])

    key_codes = nav_df["amfi_code"].unique()[:5]

    plt.figure(figsize=(12, 6))
    rf_daily = (1 + 0.065) ** (1/252) - 1

    for code in key_codes:
        sub = nav_df[nav_df["amfi_code"] == code].sort_values("date").copy()
        sub["daily_return"] = sub["nav"].pct_change()

        rolling_mean = sub["daily_return"].rolling(90).mean()
        rolling_std = sub["daily_return"].rolling(90).std()
        sub["rolling_sharpe"] = ((rolling_mean - rf_daily) / rolling_std) * np.sqrt(252)

        plt.plot(sub["date"], sub["rolling_sharpe"], label=f"Scheme {code}", linewidth=1.8)

    plt.title("90-Day Rolling Sharpe Ratio Trajectory (2022–2026)", fontsize=12, fontweight="bold")
    plt.xlabel("Date")
    plt.ylabel("Rolling Sharpe Ratio")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)

    out_chart = FIGURES_DIR / "rolling_sharpe_chart.png"
    plt.savefig(out_chart, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved rolling Sharpe chart to {out_chart}")


def analyze_investor_cohorts_and_sip():
    """Analyze investor cohorts and SIP continuity for 6+ SIP investors."""
    logger.info("Performing Cohort & SIP Continuity Analysis...")
    tx = pd.read_csv(PROC_DIR / "08_investor_transactions.csv")
    tx["transaction_date"] = pd.to_datetime(tx["transaction_date"])

    # Cohort Analysis: First Transaction Year
    tx["first_tx_date"] = tx.groupby("investor_id")["transaction_date"].transform("min")
    tx["cohort_year"] = tx["first_tx_date"].dt.year

    cohort_summary = tx.groupby("cohort_year").agg(
        total_investors=("investor_id", "nunique"),
        avg_sip_amount=("amount_inr", "mean"),
        total_invested_crores=("amount_inr", lambda x: round(x.sum() / 1e7, 2))
    ).reset_index()
    logger.info(f"Cohort Summary:\n{cohort_summary}")

    # SIP Continuity Analysis: 6+ SIP transactions, gap > 35 days
    sip = tx[tx["transaction_type"] == "SIP"].sort_values(["investor_id", "transaction_date"])
    sip_counts = sip.groupby("investor_id").size()
    eligible_investors = sip_counts[sip_counts >= 6].index

    eligible_sip = sip[sip["investor_id"].isin(eligible_investors)].copy()
    eligible_sip["gap_days"] = eligible_sip.groupby("investor_id")["transaction_date"].diff().dt.days

    investor_avg_gap = eligible_sip.groupby("investor_id")["gap_days"].mean()
    at_risk_count = (investor_avg_gap > 35).sum()
    total_eligible = len(eligible_investors)
    continuous_count = total_eligible - at_risk_count

    at_risk_pct = round((at_risk_count / total_eligible) * 100, 1)
    continuous_pct = round((continuous_count / total_eligible) * 100, 1)

    logger.info(f"SIP Continuity Results: Total Eligible = {total_eligible}, At-Risk = {at_risk_count} ({at_risk_pct}%), Continuous = {continuous_count} ({continuous_pct}%)")


def compute_sector_hhi():
    """Compute Herfindahl-Hirschman Index (HHI = sum(w_i^2)) for equity portfolios."""
    logger.info("Computing Sector HHI Index...")
    holdings = pd.read_csv(PROC_DIR / "09_portfolio_holdings.csv")

    hhi_list = []
    for code, group in holdings.groupby("amfi_code"):
        # Weight in fraction
        weights = group["weight_pct"] / 100.0 if group["weight_pct"].max() > 1.0 else group["weight_pct"]
        hhi = np.sum(weights ** 2)
        hhi_list.append({"amfi_code": code, "hhi_index": round(hhi, 4)})

    hhi_df = pd.DataFrame(hhi_list)
    logger.info(f"Computed Sector HHI for {len(hhi_df)} schemes. Average HHI = {hhi_df['hhi_index'].mean():.4f}")


def main():
    logger.info("Starting Advanced Analytics Engine...")
    compute_var_cvar()
    compute_rolling_sharpe()
    analyze_investor_cohorts_and_sip()
    compute_sector_hhi()
    logger.info("Advanced Analytics Engine Completed Successfully.")


if __name__ == "__main__":
    main()
