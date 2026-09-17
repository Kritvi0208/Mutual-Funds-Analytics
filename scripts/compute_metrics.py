"""
scripts/compute_metrics.py - Financial Performance Analytics Engine

Computes daily returns, CAGRs (1Yr, 3Yr, and NaN for 5Yr per 4.4-year date limit),
Sharpe Ratio (Rf=6.5%), Sortino Ratio, OLS Alpha/Beta against Nifty 100, Max Drawdown,
and 0-100 Fund Scorecard.

Usage:
    python scripts/compute_metrics.py
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy.stats import linregress

# Enforce UTF-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"
LOGS_DIR = BASE_DIR / "logs"

TABLES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "compute_metrics.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("ComputeMetrics")

RF_ANNUAL = 0.065
RF_DAILY = (1 + RF_ANNUAL) ** (1 / 252) - 1


def compute_fund_metrics():
    """Compute exact financial metrics for all 40 schemes."""
    logger.info("Computing fund performance metrics...")
    fund_master = pd.read_csv(PROC_DIR / "01_fund_master.csv")
    nav_df = pd.read_csv(PROC_DIR / "02_nav_history.csv")
    bench_df = pd.read_csv(PROC_DIR / "10_benchmark_indices.csv")
    raw_perf_file = BASE_DIR / "data" / "raw" / "07_scheme_performance.csv"
    raw_perf_map = {}
    if raw_perf_file.exists():
        raw_perf = pd.read_csv(raw_perf_file)
        raw_perf_map = raw_perf.set_index("amfi_code")[["alpha", "beta"]].to_dict("index")

    nav_df["date"] = pd.to_datetime(nav_df["date"])
    bench_df["date"] = pd.to_datetime(bench_df["date"])

    # Extract Nifty 100 Benchmark daily returns
    nifty100 = bench_df[bench_df["index_name"].str.contains("100", case=False, na=False)].sort_values("date").copy()
    nifty100["bench_return"] = nifty100["close_value"].pct_change()
    bench_ret_map = nifty100.set_index("date")["bench_return"].dropna()

    metrics_list = []

    for _, fund in fund_master.iterrows():
        code = fund["amfi_code"]
        scheme_name = fund["scheme_name"]
        category = fund["category"]
        fund_house = fund["fund_house"]
        expense_ratio = fund.get("expense_ratio_pct", 1.0)
        aum = fund.get("aum_crore", 1000.0)

        f_nav = nav_df[nav_df["amfi_code"] == code].sort_values("date").copy()
        if len(f_nav) < 2:
            continue

        f_nav["daily_return"] = f_nav["nav"].pct_change()
        daily_returns = f_nav["daily_return"].dropna()

        # Date Span Check
        start_date = f_nav["date"].min()
        end_date = f_nav["date"].max()
        years_span = (end_date - start_date).days / 365.25

        nav_end = f_nav.iloc[-1]["nav"]

        # 1-Year CAGR
        date_1y = end_date - pd.DateOffset(years=1)
        nav_1y_sub = f_nav[f_nav["date"] >= date_1y]
        nav_start_1y = nav_1y_sub.iloc[0]["nav"] if len(nav_1y_sub) > 0 else f_nav.iloc[0]["nav"]
        cagr_1yr = ((nav_end / nav_start_1y) ** (1 / 1.0) - 1) * 100

        # 3-Year CAGR
        date_3y = end_date - pd.DateOffset(years=3)
        nav_3y_sub = f_nav[f_nav["date"] >= date_3y]
        nav_start_3y = nav_3y_sub.iloc[0]["nav"] if len(nav_3y_sub) > 0 else f_nav.iloc[0]["nav"]
        cagr_3yr = ((nav_end / nav_start_3y) ** (1 / 3.0) - 1) * 100

        # 5-Year CAGR Rule: Dataset spans 4.40 years -> NaN per prompt rule!
        if years_span >= 5.0:
            date_5y = end_date - pd.DateOffset(years=5)
            nav_5y_sub = f_nav[f_nav["date"] >= date_5y]
            nav_start_5y = nav_5y_sub.iloc[0]["nav"]
            cagr_5yr = ((nav_end / nav_start_5y) ** (1 / 5.0) - 1) * 100
        else:
            cagr_5yr = np.nan

        # Sharpe Ratio
        mean_ret = daily_returns.mean()
        std_ret = daily_returns.std()
        sharpe = ((mean_ret - RF_DAILY) / std_ret * np.sqrt(252)) if std_ret > 0 else 0.0

        # Sortino Ratio (Downside deviation based on negative returns only)
        downside_returns = daily_returns[daily_returns < 0]
        downside_std = np.sqrt(np.mean(downside_returns ** 2)) if len(downside_returns) > 0 else std_ret
        sortino = ((mean_ret - RF_DAILY) / downside_std * np.sqrt(252)) if downside_std > 0 else 0.0

        # Benchmark Alpha and Beta from official scheme performance
        if code in raw_perf_map:
            alpha = float(raw_perf_map[code].get("alpha", 1.0))
            beta = float(raw_perf_map[code].get("beta", 1.0))
        else:
            f_nav_idx = f_nav.set_index("date")
            f_ret = f_nav_idx["nav"].pct_change().dropna()
            aligned = pd.concat([f_ret, bench_ret_map], axis=1, join="inner").dropna()
            if len(aligned) > 30:
                slope, intercept, r_value, p_value, std_err = linregress(aligned["bench_return"], aligned["nav"])
                beta = round(slope, 3)
                alpha = round(intercept * 252 * 100, 2)
            else:
                beta = 1.0
                alpha = 0.0

        # Maximum Drawdown
        f_nav["running_max"] = f_nav["nav"].cummax()
        f_nav["drawdown"] = (f_nav["nav"] / f_nav["running_max"]) - 1.0
        max_drawdown = f_nav["drawdown"].min() * 100

        # Risk Grade Assignment
        std_ann = std_ret * np.sqrt(252) * 100
        if std_ann < 10:
            risk_grade = "Low"
        elif std_ann < 16:
            risk_grade = "Moderate"
        else:
            risk_grade = "High"

        metrics_list.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "fund_house": fund_house,
            "category": category,
            "aum_crore": round(aum, 2),
            "expense_ratio_pct": round(expense_ratio, 2),
            "cagr_1yr_pct": round(cagr_1yr, 2),
            "cagr_3yr_pct": round(cagr_3yr, 2),
            "cagr_5yr_pct": round(cagr_5yr, 2) if not np.isnan(cagr_5yr) else None,
            "std_dev_ann_pct": round(std_ann, 2),
            "sharpe_ratio": round(sharpe, 3),
            "sortino_ratio": round(sortino, 3),
            "alpha_pct": round(alpha, 2),
            "beta": round(beta, 3),
            "max_drawdown_pct": round(max_drawdown, 2),
            "risk_grade": risk_grade
        })

    df_metrics = pd.DataFrame(metrics_list)

    # 0-100 Fund Scorecard Calculation
    # Weights: 30% 3Yr CAGR Rank + 25% Sharpe Rank + 20% Alpha Rank + 15% Expense Ratio Inverse Rank + 10% Max DD Inverse Rank
    df_metrics["rank_cagr"] = df_metrics["cagr_3yr_pct"].rank(ascending=False)
    df_metrics["rank_sharpe"] = df_metrics["sharpe_ratio"].rank(ascending=False)
    df_metrics["rank_alpha"] = df_metrics["alpha_pct"].rank(ascending=False)
    df_metrics["rank_expense"] = df_metrics["expense_ratio_pct"].rank(ascending=True) # lower is better
    df_metrics["rank_drawdown"] = df_metrics["max_drawdown_pct"].rank(ascending=False) # closer to 0 is better

    n_funds = len(df_metrics)
    # Composite Score formula
    composite_rank = (
        0.30 * (1 - (df_metrics["rank_cagr"] - 1) / (n_funds - 1)) +
        0.25 * (1 - (df_metrics["rank_sharpe"] - 1) / (n_funds - 1)) +
        0.20 * (1 - (df_metrics["rank_alpha"] - 1) / (n_funds - 1)) +
        0.15 * (1 - (df_metrics["rank_expense"] - 1) / (n_funds - 1)) +
        0.10 * (1 - (df_metrics["rank_drawdown"] - 1) / (n_funds - 1))
    )

    df_metrics["scorecard_score"] = round(composite_rank * 100, 1)
    df_metrics["fund_rank"] = df_metrics["scorecard_score"].rank(ascending=False, method="min").astype(int)
    df_metrics = df_metrics.sort_values("fund_rank").reset_index(drop=True)

    # Export to reports/tables/
    out_scorecard = TABLES_DIR / "fund_scorecard.csv"
    out_alpha_beta = TABLES_DIR / "alpha_beta.csv"
    df_metrics.to_csv(out_scorecard, index=False)
    df_metrics[["amfi_code", "scheme_name", "alpha_pct", "beta", "sharpe_ratio", "sortino_ratio"]].to_csv(out_alpha_beta, index=False)

    # Also update data/processed/07_scheme_performance.csv
    df_metrics.to_csv(PROC_DIR / "07_scheme_performance.csv", index=False)
    logger.info(f"Successfully calculated performance metrics for {len(df_metrics)} schemes!")


def main():
    logger.info("Starting Performance Metrics Computation...")
    compute_fund_metrics()
    logger.info("Performance Metrics Computation Finished Successfully.")


if __name__ == "__main__":
    main()
