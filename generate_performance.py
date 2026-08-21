"""
generate_performance.py - Bluestock Mutual Fund Performance & Risk Analytics Engine

Computes quantitative financial analytics across all 40 schemes:
1. Daily Returns & Return Distribution Audit
2. 1-Year, 3-Year, 5-Year CAGR
3. Risk-Adjusted Sharpe Ratio (Rf = 6.5%)
4. Downside Risk Sortino Ratio
5. OLS Regression Alpha & Beta against Nifty 100 benchmark (scipy.stats.linregress)
6. Maximum Drawdown & Worst Drawdown Period Window
7. Composite 0-100 Fund Scorecard
8. Tracking Error & Benchmark Trajectory Plotting

Exports deliverables:
- reports/tables/fund_scorecard.csv
- reports/tables/alpha_beta.csv
- reports/figures/01_top5_vs_benchmarks_3yr.png
- notebooks/Performance_Analytics.ipynb
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import nbformat as nbf

# Enforce UTF-8 output
sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

# Styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PerformanceAnalyticsEngine")


def compute_performance_metrics():
    """Calculate quantitative metrics for all 40 schemes."""
    logger.info("Loading processed datasets for performance analytics...")

    fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
    nav_history = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv")
    benchmarks = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices.csv")

    nav_history["date"] = pd.to_datetime(nav_history["date"])
    benchmarks["date"] = pd.to_datetime(benchmarks["date"])

    # 1. Prepare Benchmark Returns (Nifty 100 & Nifty 50)
    nifty100 = benchmarks[benchmarks["index_name"].str.contains("NIFTY100|100", case=False, na=False)].sort_values("date").copy()
    if nifty100.empty:
        # Fallback to NIFTY50 if NIFTY100 label is different
        nifty100 = benchmarks[benchmarks["index_name"].str.contains("NIFTY50|50", case=False, na=False)].sort_values("date").copy()

    nifty100["bench_return"] = nifty100["close_value"].pct_change()
    nifty100_returns = nifty100.set_index("date")["bench_return"].dropna()

    nifty50 = benchmarks[benchmarks["index_name"].str.contains("NIFTY50|50", case=False, na=False)].sort_values("date").copy()
    nifty50["nifty50_return"] = nifty50["close_value"].pct_change()
    nifty50_returns = nifty50.set_index("date")["nifty50_return"].dropna()

    risk_free_rate = 0.065  # 6.5% RBI Repo Rate Proxy

    results = []
    alpha_beta_list = []

    logger.info("Computing CAGR, Sharpe, Sortino, Alpha, Beta, Max Drawdown for 40 schemes...")

    for code, group in nav_history.groupby("amfi_code"):
        group = group.sort_values("date").reset_index(drop=True)
        if len(group) < 10:
            continue

        # Scheme metadata
        master_match = fund_master[fund_master["amfi_code"] == code]
        scheme_name = master_match["scheme_name"].values[0] if not master_match.empty else f"Scheme {code}"
        fund_house = master_match["fund_house"].values[0] if not master_match.empty else "Unknown"
        category = master_match["category"].values[0] if not master_match.empty else "Equity"
        expense_ratio = master_match["expense_ratio_pct"].values[0] if not master_match.empty else 1.0

        # Calculate daily returns
        group["daily_return"] = group["nav"].pct_change()
        clean_returns = group.dropna(subset=["daily_return"])

        # 1. CAGR Calculation
        start_nav = group.iloc[0]["nav"]
        end_nav = group.iloc[-1]["nav"]
        total_days = (group.iloc[-1]["date"] - group.iloc[0]["date"]).days
        years = max(total_days / 365.25, 0.1)

        cagr_overall = ((end_nav / start_nav) ** (1.0 / years)) - 1.0

        # Sub-period CAGRs (1yr, 3yr, 5yr)
        last_date = group.iloc[-1]["date"]
        
        # 1-Year CAGR
        df_1y = group[group["date"] >= (last_date - pd.DateOffset(years=1))]
        cagr_1y = ((df_1y.iloc[-1]["nav"] / df_1y.iloc[0]["nav"]) ** (1.0 / max((df_1y.iloc[-1]["date"] - df_1y.iloc[0]["date"]).days / 365.25, 0.1))) - 1.0 if len(df_1y) > 5 else cagr_overall

        # 3-Year CAGR
        df_3y = group[group["date"] >= (last_date - pd.DateOffset(years=3))]
        cagr_3y = ((df_3y.iloc[-1]["nav"] / df_3y.iloc[0]["nav"]) ** (1.0 / max((df_3y.iloc[-1]["date"] - df_3y.iloc[0]["date"]).days / 365.25, 0.1))) - 1.0 if len(df_3y) > 5 else cagr_overall

        # 5-Year CAGR
        df_5y = group[group["date"] >= (last_date - pd.DateOffset(years=5))]
        cagr_5y = ((df_5y.iloc[-1]["nav"] / df_5y.iloc[0]["nav"]) ** (1.0 / max((df_5y.iloc[-1]["date"] - df_5y.iloc[0]["date"]).days / 365.25, 0.1))) - 1.0 if len(df_5y) > 5 else cagr_overall

        # 2. Sharpe Ratio
        mean_daily_return = clean_returns["daily_return"].mean()
        std_daily_return = clean_returns["daily_return"].std()
        ann_return = mean_daily_return * 252
        ann_volatility = std_daily_return * np.sqrt(252)

        sharpe_ratio = (ann_return - risk_free_rate) / ann_volatility if ann_volatility > 0 else 0.0

        # 3. Sortino Ratio (Downside volatility)
        downside_returns = clean_returns[clean_returns["daily_return"] < 0]["daily_return"]
        downside_std = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else ann_volatility
        sortino_ratio = (ann_return - risk_free_rate) / downside_std if downside_std > 0 else 0.0

        # 4. Maximum Drawdown & Date Range Window
        group["running_max"] = group["nav"].cummax()
        group["drawdown"] = (group["nav"] / group["running_max"]) - 1.0
        max_drawdown = group["drawdown"].min()
        
        trough_idx = group["drawdown"].idxmin()
        trough_date = group.loc[trough_idx, "date"]
        peak_date = group.loc[:trough_idx, "nav"].idxmax()
        peak_date_val = group.loc[peak_date, "date"]
        drawdown_window = f"{peak_date_val.strftime('%Y-%m-%d')} to {trough_date.strftime('%Y-%m-%d')}"

        # 5. OLS Regression Alpha & Beta against Nifty 100
        fund_series = clean_returns.set_index("date")["daily_return"]
        aligned_df = pd.concat([fund_series, nifty100_returns], axis=1, join="inner").dropna()
        aligned_df.columns = ["fund_ret", "bench_ret"]

        if len(aligned_df) > 30:
            reg = stats.linregress(aligned_df["bench_ret"], aligned_df["fund_ret"])
            beta = reg.slope
            alpha_ann = reg.intercept * 252
            r_squared = reg.rvalue ** 2
            p_value = reg.pvalue
        else:
            beta = 1.0
            alpha_ann = 0.0
            r_squared = 0.0
            p_value = 1.0

        # 6. Tracking Error against Nifty 100
        if len(aligned_df) > 30:
            diff_returns = aligned_df["fund_ret"] - aligned_df["bench_ret"]
            tracking_error = diff_returns.std() * np.sqrt(252)
        else:
            tracking_error = 0.05

        results.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "fund_house": fund_house,
            "category": category,
            "expense_ratio_pct": expense_ratio,
            "cagr_1yr_pct": round(cagr_1y * 100, 2),
            "cagr_3yr_pct": round(cagr_3y * 100, 2),
            "cagr_5yr_pct": round(cagr_5y * 100, 2),
            "ann_volatility_pct": round(ann_volatility * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "alpha_pct": round(alpha_ann * 100, 2),
            "beta": round(beta, 2),
            "r_squared": round(r_squared, 4),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "drawdown_window": drawdown_window,
            "tracking_error_pct": round(tracking_error * 100, 2)
        })

        alpha_beta_list.append({
            "amfi_code": code,
            "scheme_name": scheme_name,
            "fund_house": fund_house,
            "alpha_pct": round(alpha_ann * 100, 2),
            "beta": round(beta, 2),
            "r_squared": round(r_squared, 4),
            "p_value": round(p_value, 5),
            "tracking_error_pct": round(tracking_error * 100, 2)
        })

    perf_df = pd.DataFrame(results)
    ab_df = pd.DataFrame(alpha_beta_list)

    # Export alpha_beta.csv
    ab_csv_path = TABLES_DIR / "alpha_beta.csv"
    ab_df.to_csv(ab_csv_path, index=False)
    logger.info(f"Exported alpha_beta.csv to {ab_csv_path}")

    # 7. Compute Fund Scorecard (0–100)
    # Composite: 30% x 3yr return + 25% x Sharpe + 20% x Alpha + 15% x Expense (Inverse) + 10% x Max DD (Inverse)
    perf_df["rank_return3y"] = perf_df["cagr_3yr_pct"].rank(ascending=True)
    perf_df["rank_sharpe"] = perf_df["sharpe_ratio"].rank(ascending=True)
    perf_df["rank_alpha"] = perf_df["alpha_pct"].rank(ascending=True)
    perf_df["rank_expense_inv"] = perf_df["expense_ratio_pct"].rank(ascending=False)
    perf_df["rank_maxdd_inv"] = perf_df["max_drawdown_pct"].rank(ascending=True) # less negative is better

    perf_df["raw_composite_score"] = (
        0.30 * perf_df["rank_return3y"] +
        0.25 * perf_df["rank_sharpe"] +
        0.20 * perf_df["rank_alpha"] +
        0.15 * perf_df["rank_expense_inv"] +
        0.10 * perf_df["rank_maxdd_inv"]
    )

    # Normalize raw score onto 0-100 scale
    min_raw = perf_df["raw_composite_score"].min()
    max_raw = perf_df["raw_composite_score"].max()
    perf_df["scorecard_score"] = (((perf_df["raw_composite_score"] - min_raw) / (max_raw - min_raw)) * 100).round(2)

    perf_df = perf_df.sort_values(by="scorecard_score", ascending=False).reset_index(drop=True)
    perf_df["fund_rank"] = range(1, len(perf_df) + 1)

    # Export fund_scorecard.csv
    scorecard_cols = [
        "fund_rank", "amfi_code", "scheme_name", "fund_house", "category", 
        "scorecard_score", "cagr_3yr_pct", "sharpe_ratio", "sortino_ratio", 
        "alpha_pct", "beta", "expense_ratio_pct", "max_drawdown_pct", "drawdown_window"
    ]
    scorecard_df = perf_df[scorecard_cols]
    scorecard_csv_path = TABLES_DIR / "fund_scorecard.csv"
    scorecard_df.to_csv(scorecard_csv_path, index=False)
    logger.info(f"Exported fund_scorecard.csv to {scorecard_csv_path}")

    return perf_df, nav_history, benchmarks


def generate_benchmark_comparison_chart(perf_df, nav_history, benchmarks):
    """Plot Top 5 funds vs Nifty 50 and Nifty 100 over 3 years and export PNG."""
    logger.info("Generating Top 5 Funds vs Benchmarks 3-Year Comparison Chart...")

    top_5_codes = perf_df.head(5)["amfi_code"].tolist()
    
    # Filter 3-Year date window
    max_date = nav_history["date"].max()
    min_3y_date = max_date - pd.DateOffset(years=3)

    nav_3y = nav_history[(nav_history["amfi_code"].isin(top_5_codes)) & (nav_history["date"] >= min_3y_date)].copy()
    bench_3y = benchmarks[benchmarks["date"] >= min_3y_date].copy()

    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)

    # Plot Top 5 Funds Indexed to 100
    for code in top_5_codes:
        sub = nav_3y[nav_3y["amfi_code"] == code].sort_values("date").copy()
        if not sub.empty:
            sub["rebased_nav"] = (sub["nav"] / sub.iloc[0]["nav"]) * 100
            scheme_name = perf_df[perf_df["amfi_code"] == code]["scheme_name"].values[0]
            ax.plot(sub["date"], sub["rebased_nav"], label=f"{scheme_name[:35]}...", linewidth=2.0)

    # Plot Benchmarks Rebased to 100
    nifty50 = bench_3y[bench_3y["index_name"].str.contains("50", case=False, na=False)].sort_values("date").copy()
    if not nifty50.empty:
        nifty50["rebased_bench"] = (nifty50["close_value"] / nifty50.iloc[0]["close_value"]) * 100
        ax.plot(nifty50["date"], nifty50["rebased_bench"], color="black", linestyle="--", linewidth=2.5, label="NIFTY 50 (Benchmark)")

    nifty100 = bench_3y[bench_3y["index_name"].str.contains("100", case=False, na=False)].sort_values("date").copy()
    if not nifty100.empty:
        nifty100["rebased_bench"] = (nifty100["close_value"] / nifty100.iloc[0]["close_value"]) * 100
        ax.plot(nifty100["date"], nifty100["rebased_bench"], color="red", linestyle=":", linewidth=2.5, label="NIFTY 100 (Benchmark)")

    ax.set_title("3-Year Trajectory: Top 5 Performers vs NIFTY 50 & NIFTY 100 (Rebased to 100)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=11)
    ax.set_ylabel("Normalized Growth (Base = 100)", fontsize=11)
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()

    out_png = FIGURES_DIR / "01_top5_vs_benchmarks_3yr.png"
    plt.savefig(out_png)
    plt.close()
    logger.info(f"Saved benchmark comparison chart to {out_png}")


def build_performance_notebook(perf_df):
    """Build and execute notebooks/Performance_Analytics.ipynb."""
    logger.info("Building notebooks/Performance_Analytics.ipynb...")
    nb = nbf.v4.new_notebook()

    header_md = """# Bluestock Mutual Fund Capstone Project — Fund Performance & Risk Analytics

**Author**: Ritvika Kulshreshtha  
**Date**: August 2026  
**Repository**: `Kritvi0208/Mutual-Funds-Analytics`  

---

## Executive Overview
This notebook presents quantitative risk-return modeling across all 40 mutual fund schemes in the Bluestock portfolio.

### Key Quantitative Analytics Computed:
1. **Daily Returns & Distribution**: Continuous daily percentage return series $\\text{NAV}_t / \\text{NAV}_{t-1} - 1$.
2. **Multi-Horizon CAGR**: 1-Year, 3-Year, and 5-Year Compound Annual Growth Rates.
3. **Sharpe Ratio**: Risk-adjusted return over $R_f = 6.5\\%$ (RBI repo rate proxy).
4. **Sortino Ratio**: Downside risk-adjusted return ratio measuring downside volatility.
5. **Alpha & Beta (OLS Regression)**: Linear regression against Nifty 100 ($\text{Alpha} = \text{intercept} \times 252$).
6. **Maximum Drawdown**: Peak-to-trough decline analysis and worst drawdown windows.
7. **Composite Fund Scorecard (0–100)**: Multi-metric ranking score combining returns (30%), Sharpe (25%), Alpha (20%), low cost (15%), and low drawdown (10%).
8. **Tracking Error & Benchmark Relative Performance**: Standard deviation of excess returns relative to Nifty 50 & Nifty 100.

---
"""

    summary_md = f"""## 📊 Top 10 Funds by Scorecard Composite Rating (0–100)

| Rank | AMFI Code | Scheme Name | Fund House | Score (0-100) | 3Yr CAGR | Sharpe Ratio | Sortino Ratio | Alpha | Beta | Expense Ratio |
|---|---|---|---|---|---|---|---|---|---|---|
"""
    for _, row in perf_df.head(10).iterrows():
        summary_md += f"| {int(row['fund_rank'])} | {int(row['amfi_code'])} | {row['scheme_name']} | {row['fund_house']} | **{row['scorecard_score']}** | {row['cagr_3yr_pct']}% | {row['sharpe_ratio']} | {row['sortino_ratio']} | {row['alpha_pct']}% | {row['beta']} | {row['expense_ratio_pct']}% |\n"

    code_imports = """import os
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
pd.set_option('display.max_columns', 20)
print("Performance Analytics environment initialized successfully.")
"""

    code_load_tables = """# Load Exported Performance Analytics Tables
current_dir = Path(".").resolve()
BASE_DIR = current_dir if (current_dir / "reports" / "tables").exists() else current_dir.parent
TABLES_DIR = BASE_DIR / "reports" / "tables"

scorecard_df = pd.read_csv(TABLES_DIR / "fund_scorecard.csv")
alpha_beta_df = pd.read_csv(TABLES_DIR / "alpha_beta.csv")

print(f"Loaded Fund Scorecard ({len(scorecard_df)} funds) and Alpha-Beta metrics ({len(alpha_beta_df)} funds).")
scorecard_df.head(10)
"""

    code_plot_scorecard = """# Plot Composite Scorecard Top 10 Funds
plt.figure(figsize=(12, 6))
sns.barplot(data=scorecard_df.head(10), x='scorecard_score', y='scheme_name', palette='crest')
plt.title("Top 10 Mutual Funds by Composite Performance Scorecard (0–100 Scale)", fontsize=14, fontweight='bold')
plt.xlabel("Composite Scorecard Rating (0-100)")
plt.ylabel("Scheme Name")
plt.xlim(0, 100)
plt.tight_layout()
plt.show()
"""

    code_plot_sharpe_sortino = """# Sharpe vs Sortino Ratio Comparison Scatter
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=scorecard_df, 
    x='sharpe_ratio', 
    y='sortino_ratio', 
    hue='category', 
    size='scorecard_score',
    sizes=(50, 300),
    palette='Set1'
)
plt.axhline(0, color='grey', linestyle='--')
plt.axvline(0, color='grey', linestyle='--')
plt.title("Risk-Adjusted Return Profiles: Sharpe Ratio vs Sortino Ratio", fontsize=14, fontweight='bold')
plt.xlabel("Sharpe Ratio (Total Risk)")
plt.ylabel("Sortino Ratio (Downside Risk)")
plt.tight_layout()
plt.show()
"""

    code_plot_alpha_beta = """# Alpha vs Beta Risk Profile
plt.figure(figsize=(10, 6))
sns.scatterplot(
    data=scorecard_df, 
    x='beta', 
    y='alpha_pct', 
    hue='fund_house',
    size='cagr_3yr_pct',
    sizes=(40, 350),
    palette='tab10'
)
plt.axhline(0, color='red', linestyle='--', label='Zero Alpha Baseline')
plt.axvline(1.0, color='black', linestyle=':', label='Market Beta = 1.0')
plt.title("Alpha vs Beta Scatter (OLS Regression against Nifty 100)", fontsize=14, fontweight='bold')
plt.xlabel("Beta (Systematic Market Risk)")
plt.ylabel("Annualized Alpha (%)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
"""

    # Add cells
    nb.cells.append(nbf.v4.new_markdown_cell(header_md))
    nb.cells.append(nbf.v4.new_markdown_cell(summary_md))
    nb.cells.append(nbf.v4.new_code_cell(code_imports))
    nb.cells.append(nbf.v4.new_code_cell(code_load_tables))
    nb.cells.append(nbf.v4.new_code_cell(code_plot_scorecard))
    nb.cells.append(nbf.v4.new_code_cell(code_plot_sharpe_sortino))
    nb.cells.append(nbf.v4.new_code_cell(code_plot_alpha_beta))

    out_notebook_path = NOTEBOOKS_DIR / "Performance_Analytics.ipynb"
    with open(out_notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    logger.info(f"Performance_Analytics.ipynb saved at {out_notebook_path}.")


def main():
    logger.info("Starting Fund Performance Analytics Engine...")
    perf_df, nav_history, benchmarks = compute_performance_metrics()
    generate_benchmark_comparison_chart(perf_df, nav_history, benchmarks)
    build_performance_notebook(perf_df)
    logger.info("Fund Performance Analytics Engine finished successfully.")


if __name__ == "__main__":
    main()
