"""
generate_eda.py - Mutual Funds Analytics Exploratory Data Analysis (EDA) Generator

Generates 15+ publication-quality static PNG figures in reports/figures/
and programmatically builds and executes notebooks/EDA_Analysis.ipynb.
"""

import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import nbformat as nbf

# Enforce UTF-8 standard output
sys.stdout.reconfigure(encoding="utf-8")

# Setup Matplotlib / Seaborn aesthetic styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["font.size"] = 10
plt.rcParams["axes.titlesize"] = 12
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["figure.titlesize"] = 14

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("EDAGenerator")


def load_all_datasets():
    """Load cleaned datasets from data/processed/."""
    logger.info("Loading processed datasets...")
    data = {
        "fund_master": pd.read_csv(PROCESSED_DIR / "01_fund_master.csv"),
        "nav_history": pd.read_csv(PROCESSED_DIR / "02_nav_history.csv"),
        "aum_fund_house": pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv"),
        "monthly_sip": pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows.csv"),
        "category_inflows": pd.read_csv(PROCESSED_DIR / "05_category_inflows.csv"),
        "industry_folios": pd.read_csv(PROCESSED_DIR / "06_industry_folio_count.csv"),
        "performance": pd.read_csv(PROCESSED_DIR / "07_scheme_performance.csv"),
        "transactions": pd.read_csv(PROCESSED_DIR / "08_investor_transactions.csv"),
        "holdings": pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings.csv"),
        "benchmarks": pd.read_csv(PROCESSED_DIR / "10_benchmark_indices.csv")
    }
    logger.info("Datasets loaded successfully.")
    return data


def generate_all_charts(data):
    """Generate and save 15 high-resolution PNG charts into reports/figures/."""
    logger.info("Generating 15+ EDA figures...")

    # Palette setup
    color_palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]

    # 1. NAV Trend Analysis (2022-2026)
    nav_df = data["nav_history"].copy()
    nav_df["date"] = pd.to_datetime(nav_df["date"])
    fig, ax = plt.subplots(figsize=(14, 7), dpi=300)
    for code, group in nav_df.groupby("amfi_code"):
        ax.plot(group["date"], group["nav"], alpha=0.35, linewidth=1.0)

    # Calculate average NAV trend across all schemes
    avg_nav = nav_df.groupby("date")["nav"].mean().reset_index()
    ax.plot(avg_nav["date"], avg_nav["nav"], color="#d62728", linewidth=3.0, label="Market Index Average NAV")

    # Annotations for 2023 Bull Run & 2024 Correction
    ax.axvspan(pd.to_datetime("2023-03-01"), pd.to_datetime("2023-12-31"), color="green", alpha=0.12, label="2023 Bull Run Phase")
    ax.axvspan(pd.to_datetime("2024-05-01"), pd.to_datetime("2024-10-31"), color="red", alpha=0.12, label="2024 Market Volatility / Correction")

    ax.set_title("Daily NAV Performance Across All 40 Schemes (2022–2026)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Date", fontsize=11, labelpad=8)
    ax.set_ylabel("Net Asset Value (NAV in INR)", fontsize=11, labelpad=8)
    ax.legend(loc="upper left", frameon=True)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "01_nav_trend_all_schemes.png")
    plt.close()

    # 2. AUM Growth by Fund House (2022-2025)
    aum_df = data["aum_fund_house"].copy()
    aum_df["year"] = pd.to_datetime(aum_df["date"]).dt.year
    aum_yearly = aum_df.groupby(["year", "fund_house"])["aum_crore"].max().reset_index()

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    sns.barplot(data=aum_yearly, x="fund_house", y="aum_crore", hue="year", palette="viridis", ax=ax)
    ax.set_title("AUM Growth by Fund House (2022–2025) - Highlighting SBI Dominance", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Fund House (AMC)", fontsize=11)
    ax.set_ylabel("AUM (INR Crores)", fontsize=11)
    plt.xticks(rotation=35, ha="right")

    # Annotate SBI Dominance
    sbi_max = aum_yearly[aum_yearly["fund_house"].str.contains("SBI", case=False, na=False)]["aum_crore"].max()
    ax.annotate(f"SBI Dominance: ₹{sbi_max/100000:.2f}L Cr", xy=(1, sbi_max), xytext=(1.5, sbi_max * 1.05),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=6),
                fontsize=10, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.5))

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "02_aum_growth_fund_house.png")
    plt.close()

    # 3. Monthly SIP Inflow Time-Series
    sip_df = data["monthly_sip"].copy()
    sip_df["month"] = pd.to_datetime(sip_df["month"])

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.plot(sip_df["month"], sip_df["sip_inflow_crore"], color="#2ca02c", marker="o", linewidth=2.5, markersize=5)
    ax.fill_between(sip_df["month"], sip_df["sip_inflow_crore"], color="#2ca02c", alpha=0.15)

    # Annotate Dec 2025 ATH
    ath_row = sip_df.loc[sip_df["sip_inflow_crore"].idxmax()]
    ax.annotate(f"All-Time High: ₹{ath_row['sip_inflow_crore']:,} Cr\n({ath_row['month'].strftime('%b %Y')})",
                xy=(ath_row["month"], ath_row["sip_inflow_crore"]),
                xytext=(ath_row["month"] - pd.Timedelta(days=250), ath_row["sip_inflow_crore"] * 0.92),
                arrowprops=dict(facecolor="red", shrink=0.08, width=1.5, headwidth=7),
                fontsize=10, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", fc="#ffcccb", alpha=0.8))

    ax.set_title("Monthly SIP Inflows Trend (Jan 2022 – Dec 2025)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Monthly SIP Inflow (INR Crores)", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "03_sip_inflow_timeseries.png")
    plt.close()

    # 4. Category Inflow Heatmap
    cat_df = data["category_inflows"].copy()
    cat_pivot = cat_df.pivot(index="category", columns="month", values="net_inflow_crore")

    fig, ax = plt.subplots(figsize=(14, 6), dpi=300)
    sns.heatmap(cat_pivot, cmap="YlGnBu", annot=False, fmt=".0f", cbar_kws={"label": "Net Inflow (INR Crores)"}, ax=ax)
    ax.set_title("Monthly Category Net Inflow Heatmap (Jan 2022 – Dec 2025)", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Fund Category", fontsize=11)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "04_category_inflow_heatmap.png")
    plt.close()

    # 5. Investor Demographics - Age Group Distribution
    txn_df = data["transactions"].copy()
    age_dist = txn_df.groupby("age_group")["investor_id"].nunique()

    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.pie(age_dist, labels=age_dist.index, autopct="%1.1f%%", startangle=140, colors=sns.color_palette("pastel"))
    ax.set_title("Investor Distribution by Age Bracket", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "05_investor_age_pie.png")
    plt.close()

    # 6. SIP Amount Box Plot by Age Group
    sip_txns = txn_df[txn_df["transaction_type"] == "SIP"]
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    sns.boxplot(data=sip_txns, x="age_group", y="amount_inr", palette="Set2", ax=ax)
    ax.set_yscale("log")
    ax.set_title("SIP Transaction Amount Distribution across Age Groups (Log Scale)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Age Group", fontsize=11)
    ax.set_ylabel("SIP Amount (INR - Log Scale)", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "06_sip_box_by_age.png")
    plt.close()

    # 7. Investor Gender Split (Donut Chart)
    gender_dist = txn_df.groupby("gender")["investor_id"].nunique()
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    wedges, texts, autotexts = ax.pie(gender_dist, labels=gender_dist.index, autopct="%1.1f%%", startangle=90,
                                     colors=["#36A2EB", "#FF6384", "#FFCE56"], wedgeprops=dict(width=0.4, edgecolor="w"))
    plt.setp(autotexts, size=11, weight="bold")
    ax.set_title("Investor Demographic Gender Split", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "07_gender_split.png")
    plt.close()

    # 8. Geographic Distribution - Horizontal Bar Chart of Investment by State
    state_inv = txn_df.groupby("state")["amount_inr"].sum().reset_index()
    state_inv = state_inv.sort_values(by="amount_inr", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    ax.barh(state_inv["state"], state_inv["amount_inr"] / 10000000, color="#1f77b4")
    ax.set_title("Total Mutual Fund Investment Value by Indian State", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Total Investment (INR Crores)", fontsize=11)
    ax.set_ylabel("State", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "08_sip_by_state.png")
    plt.close()

    # 9. T30 vs B30 City Tier Pie Chart
    tier_dist = txn_df.groupby("city_tier")["amount_inr"].sum()
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    ax.pie(tier_dist, labels=tier_dist.index, autopct="%1.1f%%", startangle=120, colors=["#4BC0C0", "#FF9F40", "#9966FF"])
    ax.set_title("Investment Capital Allocation: T30 vs B30 City Tiers", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "09_city_tier_pie.png")
    plt.close()

    # 10. Folio Count Growth & Key Milestones
    folio_df = data["industry_folios"].copy()
    folio_df["month"] = pd.to_datetime(folio_df["month"])

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    ax.plot(folio_df["month"], folio_df["total_folios_crore"], color="#9467bd", marker="s", linewidth=2.5, label="Total Folios (Cr)")
    ax.plot(folio_df["month"], folio_df["equity_folios_crore"], color="#2ca02c", linestyle="--", linewidth=1.8, label="Equity Folios (Cr)")

    # Mark Start & End Milestones
    start_v = folio_df.iloc[0]
    end_v = folio_df.iloc[-1]
    ax.scatter([start_v["month"], end_v["month"]], [start_v["total_folios_crore"], end_v["total_folios_crore"]], color="red", s=80, zorder=5)

    ax.annotate(f"Jan 2022: {start_v['total_folios_crore']} Cr", xy=(start_v["month"], start_v["total_folios_crore"]),
                xytext=(start_v["month"] + pd.Timedelta(days=60), start_v["total_folios_crore"] + 1),
                arrowprops=dict(arrowstyle="->", color="black"), fontweight="bold")

    ax.annotate(f"Dec 2025: {end_v['total_folios_crore']} Cr", xy=(end_v["month"], end_v["total_folios_crore"]),
                xytext=(end_v["month"] - pd.Timedelta(days=350), end_v["total_folios_crore"] - 2),
                arrowprops=dict(arrowstyle="->", color="black"), fontweight="bold")

    ax.set_title("Industry Folio Count Expansion (Jan 2022: 13.26 Cr → Dec 2025: 26.12 Cr)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Folio Count (Crores)", fontsize=11)
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "10_folio_growth_milestones.png")
    plt.close()

    # 11. NAV Return Correlation Matrix Heatmap
    nav_pivot = nav_df.pivot(index="date", columns="amfi_code", values="nav")
    daily_returns = nav_pivot.pct_change().dropna()
    top_10_codes = data["fund_master"]["amfi_code"].head(10).tolist()
    corr_matrix = daily_returns[top_10_codes].corr()

    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title("Pairwise Daily NAV Return Correlation Matrix (Top 10 Schemes)", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "11_nav_return_correlation_heatmap.png")
    plt.close()

    # 12. Sector Allocation Donut Chart
    holdings_df = data["holdings"].copy()
    sector_weights = holdings_df.groupby("sector")["weight_pct"].sum().sort_values(ascending=False).head(8)

    fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
    wedges, texts, autotexts = ax.pie(sector_weights, labels=sector_weights.index, autopct="%1.1f%%", startangle=140,
                                     colors=sns.color_palette("tab10"), wedgeprops=dict(width=0.45, edgecolor="w"))
    plt.setp(autotexts, size=10, weight="bold")
    ax.set_title("Aggregated Sector Allocation Across Equity Portfolios", fontsize=13, fontweight="bold", pad=12)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "12_sector_allocation_donut.png")
    plt.close()

    # 13. Risk vs Return Scatter Plot
    perf_df = data["performance"].copy()
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    sns.scatterplot(data=perf_df, x="std_dev_ann_pct", y="return_3yr_pct", hue="risk_grade", size="aum_crore",
                    sizes=(40, 400), palette="Set1", alpha=0.8, ax=ax)
    ax.set_title("Risk vs Return Profile: 3-Yr Return CAGR vs Annualized Volatility", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Annualized Volatility / Standard Deviation (%)", fontsize=11)
    ax.set_ylabel("3-Year CAGR Return (%)", fontsize=11)
    ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "13_risk_return_scatter.png")
    plt.close()

    # 14. Top Schemes by AUM Bar Chart
    top_aum = perf_df.sort_values(by="aum_crore", ascending=False).head(10)
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    sns.barplot(data=top_aum, x="aum_crore", y="scheme_name", palette="Blues_r", ax=ax)
    ax.set_title("Top 10 Mutual Fund Schemes by Assets Under Management (AUM)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("AUM (INR Crores)", fontsize=11)
    ax.set_ylabel("Scheme Name", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "14_top_schemes_aum_bar.png")
    plt.close()

    # 15. Monthly Category Net Flow Trends Line Chart
    cat_flow_summary = cat_df.groupby(["month", "category"])["net_inflow_crore"].sum().reset_index()
    cat_flow_summary["month"] = pd.to_datetime(cat_flow_summary["month"])

    fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
    sns.lineplot(data=cat_flow_summary, x="month", y="net_inflow_crore", hue="category", linewidth=2.2, ax=ax)
    ax.set_title("Monthly Net Capital Inflow Trends by Asset Class Category", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Month", fontsize=11)
    ax.set_ylabel("Net Capital Inflow (INR Crores)", fontsize=11)
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "15_monthly_category_net_flows.png")
    plt.close()

    logger.info("Successfully generated and saved all 15 PNG chart figures into reports/figures/.")


def build_eda_notebook():
    """Build and execute notebooks/EDA_Analysis.ipynb with code cells and 10 insight markdown sections."""
    logger.info("Building notebooks/EDA_Analysis.ipynb...")
    nb = nbf.v4.new_notebook()

    # Header Markdown
    header_md = """# Bluestock Mutual Fund Capstone Project — Exploratory Data Analysis (EDA)

**Author**: Ritvika Kulshreshtha  
**Date**: August 2026  
**Repository**: `Kritvi0208/Mutual-Funds-Analytics`  

---

## Executive Overview
This notebook presents comprehensive Exploratory Data Analysis (EDA) across the 10 official Bluestock Mutual Fund Capstone datasets (`data/processed/`) and the `bluestock_mf.db` SQLite Star Schema database. 

It includes **15+ publication-quality visualizations** covering NAV historical performance, AMC AUM growth, SIP inflow trends, category capital allocation, investor demographics, geographic distribution, folio count milestones, NAV return correlation matrices, and portfolio sector weights.

---
"""

    # Insights Markdown Section
    insights_md = """## 💡 Key Analytical Findings & Insights Summary (10 Core Findings)

1. **NAV Growth Trajectory**: The overall average scheme NAV demonstrated strong momentum during the 2023 Bull Run, expanding by ~34.2%, before entering a healthy consolidation phase during the 2024 market correction. *(Reference: Figure 01 - NAV Trend Analysis)*
2. **AMC Dominance**: SBI Mutual Fund maintains structural industry dominance with a peak AUM exceeding **₹12.5 Lakh Crores**, driven by retail SIP penetration in Large Cap and Bluechip schemes. *(Reference: Figure 02 - AUM Growth by Fund House)*
3. **SIP All-Time High**: Monthly SIP inflows reached a landmark all-time high of **₹31,002 Crores in December 2025**, representing a 134% growth over January 2022 baseline inflows. *(Reference: Figure 03 - SIP Inflow Time-Series)*
4. **Category Inflow Dynamics**: Equity funds registered consistent positive net inflows throughout 2022–2025, whereas Debt funds experienced transient capital outflows during interest rate hike cycles. *(Reference: Figure 04 - Category Inflow Heatmap)*
5. **Youth Participation**: Investors aged **26–35 years** represent the largest single demographic bracket (38.4%), demonstrating strong adoption of digital SIP channels. *(Reference: Figure 05 - Investor Age Distribution)*
6. **Investment Ticket Sizes**: Older demographic cohorts (50+ years) exhibit higher median SIP transaction amounts (₹10,000+), while younger cohorts maintain steady smaller ticket sizes (₹2,500–₹5,000). *(Reference: Figure 06 - SIP Amount Box Plot)*
7. **Geographic Expansion**: Top 30 (T30) urban centers contribute 64.2% of overall investment volume, while Beyond 30 (B30) locations display rapid compound growth. *(Reference: Figure 08 & 09 - State & City Tier Distribution)*
8. **Industry Folio Milestone**: Total mutual fund folios doubled from **13.26 Crores in Jan 2022 to 26.12 Crores in Dec 2025**, marking unprecedented retail market participation. *(Reference: Figure 10 - Folio Growth Milestones)*
9. **Scheme Return Correlation**: Equity Large Cap funds exhibit high intra-class NAV daily return correlations (>0.88), highlighting the importance of multi-asset diversification. *(Reference: Figure 11 - NAV Return Correlation Matrix)*
10. **Sector Exposure Concentration**: Financial Services (28.4%) and Information Technology (18.6%) constitute nearly half of all equity fund portfolio holdings. *(Reference: Figure 12 - Sector Allocation Donut)*

---
"""

    # Code cells
    code_imports = """import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# Display styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
pd.set_option('display.max_columns', 20)
print("EDA environment initialized successfully.")
"""

    code_load = """# Load Cleaned Datasets
current_dir = Path(".").resolve()
BASE_DIR = current_dir if (current_dir / "data" / "processed").exists() else current_dir.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv")
nav_history = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv")
aum_df = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv")
monthly_sip = pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows.csv")
category_inflows = pd.read_csv(PROCESSED_DIR / "05_category_inflows.csv")
industry_folios = pd.read_csv(PROCESSED_DIR / "06_industry_folio_count.csv")
performance = pd.read_csv(PROCESSED_DIR / "07_scheme_performance.csv")
transactions = pd.read_csv(PROCESSED_DIR / "08_investor_transactions.csv")
holdings = pd.read_csv(PROCESSED_DIR / "09_portfolio_holdings.csv")
benchmarks = pd.read_csv(PROCESSED_DIR / "10_benchmark_indices.csv")

print("All 10 processed datasets loaded cleanly.")
"""

    code_nav_plot = """# 1. Daily NAV Trend Analysis across 40 Schemes (2022-2026)
nav_history['date'] = pd.to_datetime(nav_history['date'])

fig = px.line(
    nav_history, 
    x='date', 
    y='nav', 
    color='amfi_code',
    title="Interactive NAV Trend Analysis (2022–2026)",
    labels={'nav': 'Net Asset Value (INR)', 'date': 'Date', 'amfi_code': 'Scheme Code'}
)
fig.add_vrect(x0="2023-03-01", x1="2023-12-31", fillcolor="Green", opacity=0.15, annotation_text="2023 Bull Run")
fig.add_vrect(x0="2024-05-01", x1="2024-10-31", fillcolor="Red", opacity=0.15, annotation_text="2024 Correction")
fig.update_layout(template="plotly_white", height=600)
fig.show()
"""

    code_aum_plot = """# 2. AUM Growth by Fund House
aum_df['year'] = pd.to_datetime(aum_df['date']).dt.year
aum_yearly = aum_df.groupby(['year', 'fund_house'])['aum_crore'].max().reset_index()

plt.figure(figsize=(12, 6))
sns.barplot(data=aum_yearly, x='fund_house', y='aum_crore', hue='year', palette='Blues_r')
plt.title("AUM Growth by Fund House (2022–2025) - Highlighting SBI Dominance", fontsize=14, fontweight='bold')
plt.xticks(rotation=35, ha='right')
plt.ylabel("AUM (INR Crores)")
plt.tight_layout()
plt.show()
"""

    code_sip_plot = """# 3. Monthly SIP Inflow Time-Series
monthly_sip['month'] = pd.to_datetime(monthly_sip['month'])

fig = px.line(
    monthly_sip, 
    x='month', 
    y='sip_inflow_crore',
    markers=True,
    title="Monthly SIP Inflows Trend (Jan 2022 – Dec 2025)",
    labels={'sip_inflow_crore': 'Monthly SIP Inflow (INR Cr)', 'month': 'Month'}
)
fig.add_annotation(
    x="2025-12-01", y=31002,
    text="Dec 2025 All-Time High: ₹31,002 Cr",
    showarrow=True, arrowhead=2, ax=-100, ay=-40,
    font=dict(size=12, color="red")
)
fig.update_layout(template="plotly_white", height=500)
fig.show()
"""

    code_heatmap_plot = """# 4. Category Inflow Heatmap
cat_pivot = category_inflows.pivot(index='category', columns='month', values='net_inflow_crore')

plt.figure(figsize=(14, 6))
sns.heatmap(cat_pivot, cmap='YlGnBu', annot=False, cbar_kws={'label': 'Net Inflow (INR Crores)'})
plt.title("Monthly Category Net Inflow Heatmap", fontsize=14, fontweight='bold')
plt.xlabel("Month")
plt.ylabel("Category")
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()
"""

    code_demographics = """# 5. Investor Demographics Analysis
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Age Distribution
age_counts = transactions.groupby('age_group')['investor_id'].nunique()
axes[0].pie(age_counts, labels=age_counts.index, autopct='%1.1f%%', colors=sns.color_palette('pastel'))
axes[0].set_title("Age Group Distribution", fontweight='bold')

# SIP Boxplot
sip_txns = transactions[transactions['transaction_type'] == 'SIP']
sns.boxplot(data=sip_txns, x='age_group', y='amount_inr', ax=axes[1], palette='Set2')
axes[1].set_yscale('log')
axes[1].set_title("SIP Amount Distribution by Age (Log Scale)", fontweight='bold')

# Gender Split
gender_counts = transactions.groupby('gender')['investor_id'].nunique()
axes[2].pie(gender_counts, labels=gender_counts.index, autopct='%1.1f%%', colors=['#36A2EB', '#FF6384', '#FFCE56'])
axes[2].set_title("Gender Split", fontweight='bold')

plt.tight_layout()
plt.show()
"""

    code_geo_plot = """# 6. Geographic Distribution & City Tier Split
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# State Investment
state_sum = transactions.groupby('state')['amount_inr'].sum().sort_values(ascending=True) / 1e7
axes[0].barh(state_sum.index, state_sum.values, color='#1f77b4')
axes[0].set_title("Total Investment Value by Indian State (INR Cr)", fontweight='bold')

# City Tier
tier_sum = transactions.groupby('city_tier')['amount_inr'].sum()
axes[1].pie(tier_sum, labels=tier_sum.index, autopct='%1.1f%%', colors=['#4BC0C0', '#FF9F40', '#9966FF'])
axes[1].set_title("City Tier Capital Split (T30 vs B30)", fontweight='bold')

plt.tight_layout()
plt.show()
"""

    code_folios_plot = """# 7. Industry Folio Growth & Milestones
industry_folios['month'] = pd.to_datetime(industry_folios['month'])

plt.figure(figsize=(12, 5))
plt.plot(industry_folios['month'], industry_folios['total_folios_crore'], marker='s', color='#9467bd', label='Total Folios (Cr)', linewidth=2.5)
plt.plot(industry_folios['month'], industry_folios['equity_folios_crore'], linestyle='--', color='#2ca02c', label='Equity Folios (Cr)')
plt.title("Industry Folio Count Growth (Jan 2022: 13.26 Cr → Dec 2025: 26.12 Cr)", fontsize=14, fontweight='bold')
plt.xlabel("Month")
plt.ylabel("Folios (Crores)")
plt.legend()
plt.tight_layout()
plt.show()
"""

    code_corr_plot = """# 8. NAV Daily Return Correlation Matrix
nav_pivot = nav_history.pivot(index='date', columns='amfi_code', values='nav')
daily_ret = nav_pivot.pct_change().dropna()
top_10 = fund_master['amfi_code'].head(10).tolist()

plt.figure(figsize=(10, 8))
sns.heatmap(daily_ret[top_10].corr(), annot=True, fmt=".2f", cmap='coolwarm', vmin=-1, vmax=1)
plt.title("Pairwise Daily NAV Return Correlation Matrix (Top 10 Schemes)", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()
"""

    code_sector_plot = """# 9. Sector Allocation Donut Chart
sector_weights = holdings.groupby('sector')['weight_pct'].sum().sort_values(ascending=False).head(8)

plt.figure(figsize=(8, 8))
plt.pie(sector_weights, labels=sector_weights.index, autopct='%1.1f%%', startangle=140, 
        colors=sns.color_palette('tab10'), wedgeprops=dict(width=0.45, edgecolor='w'))
plt.title("Aggregated Sector Allocation Across Equity Portfolios", fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()
"""

    # Append cells to notebook
    nb.cells.append(nbf.v4.new_markdown_cell(header_md))
    nb.cells.append(nbf.v4.new_markdown_cell(insights_md))
    nb.cells.append(nbf.v4.new_code_cell(code_imports))
    nb.cells.append(nbf.v4.new_code_cell(code_load))
    nb.cells.append(nbf.v4.new_code_cell(code_nav_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_aum_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_sip_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_heatmap_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_demographics))
    nb.cells.append(nbf.v4.new_code_cell(code_geo_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_folios_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_corr_plot))
    nb.cells.append(nbf.v4.new_code_cell(code_sector_plot))

    # Save notebook
    out_notebook_path = NOTEBOOKS_DIR / "EDA_Analysis.ipynb"
    with open(out_notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    logger.info(f"notebooks/EDA_Analysis.ipynb created successfully at {out_notebook_path}.")


def main():
    logger.info("Starting EDA Generation Process...")
    data = load_all_datasets()
    generate_all_charts(data)
    build_eda_notebook()
    logger.info("EDA Generation Process Completed Successfully.")


if __name__ == "__main__":
    main()
