"""
generate_powerbi_dashboard.py - Bluestock Mutual Fund 4-Page Dashboard & PDF Generator

Programmatically renders 4 high-resolution dashboard page views with Bluestock visual styling:
Page 1: Industry Overview
Page 2: Fund Performance
Page 3: Investor Analytics
Page 4: SIP & Market Trends

Exports:
- reports/figures/page1_industry_overview.png
- reports/figures/page2_fund_performance.png
- reports/figures/page3_investor_analytics.png
- reports/figures/page4_sip_market_trends.png
- reports/Dashboard.pdf
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Enforce UTF-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
REPORTS_DIR = BASE_DIR / "reports"

FIGURES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Styling Palette
NAVY = "#1E3A8A"
SLATE = "#475569"
BLUE = "#2563EB"
GREEN = "#10B981"
RED = "#EF4444"
BG_COLOR = "#F8FAFC"
CARD_BG = "#FFFFFF"

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("DashboardGenerator")


def load_all_data():
    """Load all cleaned processed datasets."""
    logger.info("Loading datasets for dashboard rendering...")
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
    scorecard = pd.read_csv(TABLES_DIR / "fund_scorecard.csv") if (TABLES_DIR / "fund_scorecard.csv").exists() else performance

    return {
        "fund_master": fund_master,
        "nav_history": nav_history,
        "aum_df": aum_df,
        "monthly_sip": monthly_sip,
        "category_inflows": category_inflows,
        "industry_folios": industry_folios,
        "performance": performance,
        "transactions": transactions,
        "holdings": holdings,
        "benchmarks": benchmarks,
        "scorecard": scorecard
    }


def draw_card(ax, title, value, subtext, color="#1E3A8A"):
    """Helper to draw KPI cards."""
    ax.set_facecolor(CARD_BG)
    ax.axis("off")
    # Border
    rect = plt.Rectangle((0.02, 0.05), 0.96, 0.9, fill=True, facecolor="#F8FAFC", edgecolor="#CBD5E1", linewidth=1.5, transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(0.08, 0.68, title, transform=ax.transAxes, fontsize=10, fontweight="bold", color=SLATE)
    ax.text(0.08, 0.35, value, transform=ax.transAxes, fontsize=18, fontweight="bold", color=color)
    ax.text(0.08, 0.15, subtext, transform=ax.transAxes, fontsize=9, color="#64748B")


def render_page1(data):
    """Render Page 1: Industry Overview."""
    logger.info("Rendering Page 1: Industry Overview...")
    fig = plt.figure(figsize=(14, 8.5), dpi=300, facecolor=BG_COLOR)

    # Title
    fig.suptitle("BLUESTOCK MUTUAL FUND ANALYTICS — PAGE 1: INDUSTRY OVERVIEW", fontsize=16, fontweight="bold", color=NAVY, y=0.97)

    # 4 KPI Cards
    gs = fig.add_gridspec(3, 4, height_ratios=[0.5, 1.2, 1.3], hspace=0.35, wspace=0.25, left=0.05, right=0.95, top=0.91, bottom=0.06)

    ax_kpi1 = fig.add_subplot(gs[0, 0])
    draw_card(ax_kpi1, "TOTAL INDUSTRY AUM", "₹81.4L Cr", "▲ SBI Peak: ₹12.5L Cr", NAVY)

    ax_kpi2 = fig.add_subplot(gs[0, 1])
    monthly_sip = data["monthly_sip"]
    ath_val = monthly_sip["sip_inflow_crore"].max() if not monthly_sip.empty else 31002
    draw_card(ax_kpi2, "MONTHLY SIP INFLOWS", f"₹{ath_val:,.0f} Cr", "▲ Dec 2025 All-Time High", GREEN)

    ax_kpi3 = fig.add_subplot(gs[0, 2])
    industry_folios = data["industry_folios"]
    latest_folios = industry_folios["total_folios_crore"].iloc[-1] if not industry_folios.empty else 26.12
    draw_card(ax_kpi3, "TOTAL INDUSTRY FOLIOS", f"{latest_folios:.2f} Cr", "▲ Doubled from 13.26 Cr", BLUE)

    ax_kpi4 = fig.add_subplot(gs[0, 3])
    draw_card(ax_kpi4, "ANALYZED SCHEMES", "40 Funds", "100% Star Schema Covered", "#4F46E5")

    # Chart 1: Industry AUM Trend (Line Chart)
    ax_aum = fig.add_subplot(gs[1, :2])
    aum_df = data["aum_df"].copy()
    aum_df["date"] = pd.to_datetime(aum_df["date"])
    aum_total = aum_df.groupby("date")["aum_crore"].sum().reset_index()
    ax_aum.plot(aum_total["date"], aum_total["aum_crore"] / 100000, color=BLUE, linewidth=2.5, marker="o", markersize=4)
    ax_aum.set_title("Industry AUM Expansion Trend (2022–2025)", fontsize=11, fontweight="bold", color=NAVY)
    ax_aum.set_ylabel("AUM (Lakh Crores)", fontsize=9)

    # Chart 2: AUM by AMC (Bar Chart)
    ax_amc = fig.add_subplot(gs[1, 2:])
    aum_latest = aum_df[aum_df["date"] == aum_df["date"].max()].sort_values("aum_crore", ascending=False)
    sns.barplot(data=aum_latest, x="aum_crore", y="fund_house", palette="Blues_r", ax=ax_amc)
    ax_amc.set_title("Assets Under Management (AUM) by Fund House (AMC)", fontsize=11, fontweight="bold", color=NAVY)
    ax_amc.set_xlabel("AUM (INR Crores)", fontsize=9)

    # Chart 3: Folio Count Growth Trend
    ax_folio = fig.add_subplot(gs[2, :])
    folio_df = industry_folios.copy()
    folio_df["month"] = pd.to_datetime(folio_df["month"])
    ax_folio.plot(folio_df["month"], folio_df["total_folios_crore"], color="#9467bd", marker="s", linewidth=2.2, label="Total Folios (Cr)")
    ax_folio.plot(folio_df["month"], folio_df["equity_folios_crore"], color=GREEN, linestyle="--", linewidth=1.8, label="Equity Folios (Cr)")
    ax_folio.set_title("Industry Folio Count Expansion (Jan 2022: 13.26 Cr → Dec 2025: 26.12 Cr)", fontsize=11, fontweight="bold", color=NAVY)
    ax_folio.set_ylabel("Folios (Crores)", fontsize=9)
    ax_folio.legend(loc="upper left")

    out_p1 = FIGURES_DIR / "page1_industry_overview.png"
    plt.savefig(out_p1, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved Page 1 screenshot to {out_p1}")


def render_page2(data):
    """Render Page 2: Fund Performance."""
    logger.info("Rendering Page 2: Fund Performance...")
    fig = plt.figure(figsize=(14, 8.5), dpi=300, facecolor=BG_COLOR)
    fig.suptitle("BLUESTOCK MUTUAL FUND ANALYTICS — PAGE 2: FUND PERFORMANCE", fontsize=16, fontweight="bold", color=NAVY, y=0.97)

    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.2], hspace=0.35, wspace=0.25, left=0.05, right=0.95, top=0.91, bottom=0.06)

    # Chart 1: Risk vs Return Scatter Plot
    ax_scatter = fig.add_subplot(gs[0, 0])
    perf = data["performance"]
    y_col = "cagr_3yr_pct" if "cagr_3yr_pct" in perf.columns else "return_3yr_pct"
    hue_col = "risk_grade" if "risk_grade" in perf.columns else ("risk_category" if "risk_category" in perf.columns else "category")
    sns.scatterplot(data=perf, x="std_dev_ann_pct", y=y_col, hue=hue_col, size="aum_crore", sizes=(40, 300), palette="Set1", ax=ax_scatter)
    ax_scatter.set_title("Risk vs Return Profile (3-Yr CAGR vs Volatility, Size = AUM)", fontsize=11, fontweight="bold", color=NAVY)
    ax_scatter.set_xlabel("Annualized Volatility (%)", fontsize=9)
    ax_scatter.set_ylabel("3-Year CAGR Return (%)", fontsize=9)

    # Chart 2: Top Funds Scorecard Table Visualization
    ax_table = fig.add_subplot(gs[0, 1])
    ax_table.axis("off")
    ax_table.set_title("Top 8 Funds Scorecard Rating Table", fontsize=11, fontweight="bold", color=NAVY, pad=10)
    sc = data["scorecard"].head(8)
    table_data = [["Rank", "Scheme Name", "Score", "3Yr CAGR", "Sharpe", "Alpha"]]
    for _, r in sc.iterrows():
        table_data.append([
            str(int(r.get("fund_rank", 1))),
            str(r["scheme_name"])[:26],
            f"{r['scorecard_score']:.1f}",
            f"{r['cagr_3yr_pct']}%",
            f"{r['sharpe_ratio']:.2f}",
            f"{r['alpha_pct']}%"
        ])
    t = ax_table.table(cellText=table_data, loc="center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(8.5)
    t.scale(1.0, 1.3)
    for (row, col), cell in t.get_celld().items():
        if row == 0:
            cell.set_facecolor(NAVY)
            cell.set_text_props(color="white", weight="bold")
        else:
            cell.set_facecolor("#F8FAFC" if row % 2 == 0 else "white")

    # Chart 3: NAV Performance vs Benchmark
    ax_nav = fig.add_subplot(gs[1, :])
    nav_df = data["nav_history"].copy()
    nav_df["date"] = pd.to_datetime(nav_df["date"])
    benchmarks = data["benchmarks"].copy()
    benchmarks["date"] = pd.to_datetime(benchmarks["date"])

    top_code = perf.sort_values("aum_crore", ascending=False).iloc[0]["amfi_code"]
    top_nav = nav_df[nav_df["amfi_code"] == top_code].sort_values("date")
    top_nav["rebased"] = (top_nav["nav"] / top_nav.iloc[0]["nav"]) * 100

    nifty50 = benchmarks[benchmarks["index_name"].str.contains("50", case=False, na=False)].sort_values("date")
    nifty50["rebased"] = (nifty50["close_value"] / nifty50.iloc[0]["close_value"]) * 100

    ax_nav.plot(top_nav["date"], top_nav["rebased"], label="Top Scheme NAV (Rebased)", color=BLUE, linewidth=2.2)
    ax_nav.plot(nifty50["date"], nifty50["rebased"], label="Nifty 50 Index (Benchmark)", color="red", linestyle="--", linewidth=2.0)
    ax_nav.set_title("Scheme NAV Trajectory vs Nifty 50 Benchmark (Rebased to 100)", fontsize=11, fontweight="bold", color=NAVY)
    ax_nav.set_ylabel("Normalized NAV", fontsize=9)
    ax_nav.legend(loc="upper left")

    out_p2 = FIGURES_DIR / "page2_fund_performance.png"
    plt.savefig(out_p2, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved Page 2 screenshot to {out_p2}")


def render_page3(data):
    """Render Page 3: Investor Analytics."""
    logger.info("Rendering Page 3: Investor Analytics...")
    fig = plt.figure(figsize=(14, 8.5), dpi=300, facecolor=BG_COLOR)
    fig.suptitle("BLUESTOCK MUTUAL FUND ANALYTICS — PAGE 3: INVESTOR ANALYTICS", fontsize=16, fontweight="bold", color=NAVY, y=0.97)

    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.2], hspace=0.35, wspace=0.25, left=0.05, right=0.95, top=0.91, bottom=0.06)

    txn = data["transactions"].copy()

    # Chart 1: Transaction Amount by State
    ax_state = fig.add_subplot(gs[0, 0])
    state_sum = txn.groupby("state")["amount_inr"].sum().sort_values(ascending=True) / 1e7
    ax_state.barh(state_sum.index, state_sum.values, color=BLUE)
    ax_state.set_title("Total Investment Value by State (INR Crores)", fontsize=11, fontweight="bold", color=NAVY)
    ax_state.set_xlabel("Investment Value (Cr)", fontsize=9)

    # Chart 2: Transaction Type Split (Donut Chart)
    ax_donut = fig.add_subplot(gs[0, 1])
    type_sum = txn.groupby("transaction_type")["amount_inr"].sum()
    ax_donut.pie(type_sum, labels=type_sum.index, autopct="%1.1f%%", startangle=140, colors=sns.color_palette("pastel"), wedgeprops=dict(width=0.45))
    ax_donut.set_title("Capital Allocation by Transaction Type", fontsize=11, fontweight="bold", color=NAVY)

    # Chart 3: Age Group vs Avg SIP Amount
    ax_age = fig.add_subplot(gs[1, 0])
    sip_txns = txn[txn["transaction_type"] == "SIP"]
    age_sip = sip_txns.groupby("age_group")["amount_inr"].mean().reset_index()
    sns.barplot(data=age_sip, x="age_group", y="amount_inr", palette="Set2", ax=ax_age)
    ax_age.set_title("Average SIP Amount by Investor Age Group (INR)", fontsize=11, fontweight="bold", color=NAVY)
    ax_age.set_ylabel("Avg SIP Amount (INR)", fontsize=9)

    # Chart 4: Monthly Transaction Volume Line
    ax_vol = fig.add_subplot(gs[1, 1])
    txn["month"] = pd.to_datetime(txn["transaction_date"]).dt.to_period("M").dt.to_timestamp()
    monthly_vol = txn.groupby("month")["transaction_id"].count().reset_index() if "transaction_id" in txn.columns else txn.groupby("month")["amount_inr"].count().reset_index()
    ax_vol.plot(monthly_vol["month"], monthly_vol.iloc[:, 1], color=GREEN, marker="o", linewidth=2.0)
    ax_vol.set_title("Monthly Investor Transaction Volume", fontsize=11, fontweight="bold", color=NAVY)
    ax_vol.set_ylabel("Transaction Count", fontsize=9)

    out_p3 = FIGURES_DIR / "page3_investor_analytics.png"
    plt.savefig(out_p3, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved Page 3 screenshot to {out_p3}")


def render_page4(data):
    """Render Page 4: SIP & Market Trends."""
    logger.info("Rendering Page 4: SIP & Market Trends...")
    fig = plt.figure(figsize=(14, 8.5), dpi=300, facecolor=BG_COLOR)
    fig.suptitle("BLUESTOCK MUTUAL FUND ANALYTICS — PAGE 4: SIP & MARKET TRENDS", fontsize=16, fontweight="bold", color=NAVY, y=0.97)

    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1.2], hspace=0.35, wspace=0.25, left=0.05, right=0.95, top=0.91, bottom=0.06)

    # Chart 1: Dual-Axis SIP Inflow + Nifty 50
    ax_dual1 = fig.add_subplot(gs[0, :])
    sip_df = data["monthly_sip"].copy()
    sip_df["month"] = pd.to_datetime(sip_df["month"])

    bench_df = data["benchmarks"].copy()
    bench_df["date"] = pd.to_datetime(bench_df["date"])
    nifty50_bench = bench_df[bench_df["index_name"].str.contains("50", case=False, na=False)].sort_values("date").copy()
    nifty50_bench["month"] = nifty50_bench["date"].dt.to_period("M").dt.to_timestamp()
    nifty = nifty50_bench.groupby("month")["close_value"].first().reset_index()

    aligned = pd.merge(sip_df, nifty, on="month", how="inner")

    ax_dual1.bar(aligned["month"], aligned["sip_inflow_crore"], width=20, color="#93C5FD", label="Monthly SIP Inflow (INR Cr)")
    ax_dual1.set_ylabel("SIP Inflow (INR Crores)", color=BLUE, fontsize=9)

    ax_dual2 = ax_dual1.twinx()
    ax_dual2.plot(aligned["month"], aligned["close_value"], color=RED, linewidth=2.5, marker="s", label="Nifty 50 Index")
    ax_dual2.set_ylabel("Nifty 50 Closing Index", color=RED, fontsize=9)
    ax_dual1.set_title("Dual-Axis Trajectory: Monthly SIP Inflows vs Nifty 50 Benchmark (2022–2025)", fontsize=11, fontweight="bold", color=NAVY)

    # Chart 2: Category Inflow Heatmap
    ax_heat = fig.add_subplot(gs[1, 0])
    cat_df = data["category_inflows"].copy()
    cat_pivot = cat_df.pivot(index="category", columns="month", values="net_inflow_crore")
    sns.heatmap(cat_pivot, cmap="YlGnBu", annot=False, cbar=False, ax=ax_heat)
    ax_heat.set_title("Monthly Category Net Inflow Heatmap", fontsize=11, fontweight="bold", color=NAVY)
    ax_heat.tick_params(axis='x', rotation=45, labelsize=7)

    # Chart 3: Top Categories by Net Inflow
    ax_top_cat = fig.add_subplot(gs[1, 1])
    top_cat = cat_df.groupby("category")["net_inflow_crore"].sum().sort_values(ascending=False).head(5).reset_index()
    sns.barplot(data=top_cat, x="net_inflow_crore", y="category", palette="Greens_r", ax=ax_top_cat)
    ax_top_cat.set_title("Top 5 Asset Categories by Cumulative Net Capital Inflow", fontsize=11, fontweight="bold", color=NAVY)
    ax_top_cat.set_xlabel("Net Capital Inflow (INR Crores)", fontsize=9)

    out_p4 = FIGURES_DIR / "page4_sip_market_trends.png"
    plt.savefig(out_p4, bbox_inches="tight")
    plt.close()
    logger.info(f"Saved Page 4 screenshot to {out_p4}")


def export_dashboard_pdf():
    """Build reports/Dashboard.pdf combining all 4 page PNG screenshots."""
    logger.info("Combining 4 page screenshots into reports/Dashboard.pdf...")
    out_pdf = REPORTS_DIR / "Dashboard.pdf"

    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=landscape(letter),
        leftMargin=0.2 * inch,
        rightMargin=0.2 * inch,
        topMargin=0.2 * inch,
        bottomMargin=0.2 * inch
    )

    story = []

    pages = [
        FIGURES_DIR / "page1_industry_overview.png",
        FIGURES_DIR / "page2_fund_performance.png",
        FIGURES_DIR / "page3_investor_analytics.png",
        FIGURES_DIR / "page4_sip_market_trends.png"
    ]

    for p in pages:
        if p.exists():
            story.append(Image(str(p), width=10.5 * inch, height=7.2 * inch))

    doc.build(story)
    logger.info(f"Successfully generated reports/Dashboard.pdf at {out_pdf}")


def main():
    logger.info("Starting Power BI Dashboard Engine...")
    data = load_all_data()
    render_page1(data)
    render_page2(data)
    render_page3(data)
    render_page4(data)
    export_dashboard_pdf()
    logger.info("Power BI Dashboard Engine Completed Successfully.")


if __name__ == "__main__":
    main()
