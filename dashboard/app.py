"""
dashboard/app.py - Bluestock Mutual Fund Analytics Interactive Web Application

A modern Streamlit web dashboard with a clean Light Pastel theme providing:
- Executive Mutual Fund Analytics & Industry KPIs
- Fund Performance Scorecard & Interactive Explorer (0–100 Rating Scale)
- Risk & Return Quantitative Modeling (Sharpe, Alpha, Beta, VaR/CVaR)
- Interactive SIP Wealth Growth Calculator
- Smart Rule-Based Fund Recommender Engine

To Run Locally:
    streamlit run dashboard/app.py
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Enforce UTF-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"
FIGURES_DIR = BASE_DIR / "reports" / "figures"

sys.path.append(str(BASE_DIR))
try:
    from recommender import recommend_funds
except ImportError:
    try:
        from scripts.recommender import recommend_funds
    except ImportError:
        recommend_funds = None

# Page Config
st.set_page_config(
    page_title="Bluestock Mutual Fund Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Light Pastel CSS Styling
st.markdown("""
<style>
    /* Global Light Theme */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    /* Header Styles */
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: #334155;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    
    /* Pastel KPI Cards */
    .kpi-card-blue {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 1px solid #BFDBFE;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.06);
    }
    .kpi-card-green {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        border: 1px solid #BBF7D0;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(34, 197, 94, 0.06);
    }
    .kpi-card-purple {
        background: linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 100%);
        border: 1px solid #E9D5FF;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(168, 85, 247, 0.06);
    }
    .kpi-card-amber {
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1px solid #FDE68A;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.06);
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #0F172A;
        margin-top: 4px;
        margin-bottom: 2px;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #475569;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-badge {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 20px;
        margin-top: 6px;
    }
    .badge-green {
        background-color: #DCFCE7;
        color: #15803D;
    }
    .badge-blue {
        background-color: #DBEAFE;
        color: #1D4ED8;
    }
    .badge-purple {
        background-color: #F3E8FF;
        color: #7E22CE;
    }
    .badge-amber {
        background-color: #FEF3C7;
        color: #B45309;
    }
    
    /* Pastel Content Cards */
    .pastel-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 14px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9;
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# Pastel Color Palette for Charts
PASTEL_PALETTE = [
    "#93C5FD",  # Pastel Blue
    "#86EFAC",  # Pastel Green
    "#FCA5A5",  # Pastel Red/Coral
    "#FDE047",  # Pastel Yellow
    "#C4B5FD",  # Pastel Purple
    "#FDBA74",  # Pastel Orange
    "#6EE7B7",  # Pastel Mint
    "#F9A8D4",  # Pastel Pink
    "#A5F3FC",  # Pastel Cyan
    "#D8B4FE",  # Pastel Lavender
]


@st.cache_data
def load_dashboard_data():
    """Load and cache processed datasets and analytical reports."""
    fund_master = pd.read_csv(PROCESSED_DIR / "01_fund_master.csv") if (PROCESSED_DIR / "01_fund_master.csv").exists() else pd.DataFrame()
    nav_history = pd.read_csv(PROCESSED_DIR / "02_nav_history.csv") if (PROCESSED_DIR / "02_nav_history.csv").exists() else pd.DataFrame()
    monthly_sip = pd.read_csv(PROCESSED_DIR / "04_monthly_sip_inflows.csv") if (PROCESSED_DIR / "04_monthly_sip_inflows.csv").exists() else pd.DataFrame()
    scorecard_df = pd.read_csv(TABLES_DIR / "fund_scorecard.csv") if (TABLES_DIR / "fund_scorecard.csv").exists() else pd.DataFrame()
    var_df = pd.read_csv(TABLES_DIR / "var_cvar_report.csv") if (TABLES_DIR / "var_cvar_report.csv").exists() else pd.DataFrame()
    aum_amc = pd.read_csv(PROCESSED_DIR / "03_aum_by_fund_house.csv") if (PROCESSED_DIR / "03_aum_by_fund_house.csv").exists() else pd.DataFrame()

    return fund_master, nav_history, monthly_sip, scorecard_df, var_df, aum_amc


fund_master, nav_history, monthly_sip, scorecard_df, var_df, aum_amc = load_dashboard_data()

# Header Section
st.markdown('<div class="main-header">📈 Bluestock Mutual Fund Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Institutional Portfolio Analytics • Risk-Adjusted Modeling • Smart Fund Recommender</div>', unsafe_allow_html=True)

# Sidebar Filter Navigation
st.sidebar.markdown("### 🧭 Navigation & Views")

nav_selection = st.sidebar.radio(
    "Select View",
    ["Executive Overview", "Fund Scorecard & Explorer", "Risk & Return Analytics", "SIP Calculator", "Smart Fund Recommender"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="background-color:#EFF6FF; border:1px solid #BFDBFE; padding:14px; border-radius:10px; font-size:0.85rem; color:#1E40AF;">
    💡 <b>Capstone Scope:</b><br>
    • 40 Key Mutual Funds<br>
    • 64,320 Cleaned Daily NAVs<br>
    • 32,778 Investor Transactions<br>
    • 10 Star Schema Tables
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 1. Executive Overview View
# ==============================================================================
if nav_selection == "Executive Overview":
    st.markdown("#### 📊 Industry Health & Key Metrics")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class="kpi-card-blue">
            <div class="metric-label">Industry Benchmark AUM</div>
            <div class="metric-value">₹81.4L Cr</div>
            <div class="metric-badge badge-blue">▲ Dec 2025 Record Peak</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="kpi-card-green">
            <div class="metric-label">Monthly SIP Inflow Peak</div>
            <div class="metric-value">₹31,002 Cr</div>
            <div class="metric-badge badge-green">▲ Dec 2025 All-Time High</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="kpi-card-purple">
            <div class="metric-label">Total Active Folios</div>
            <div class="metric-value">26.12 Cr</div>
            <div class="metric-badge badge-purple">▲ +97% (13.26 Cr → 26.12 Cr)</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="kpi-card-amber">
            <div class="metric-label">Analyzed Schemes</div>
            <div class="metric-value">40 Schemes</div>
            <div class="metric-badge badge-amber">100% Star Schema Covered</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        if not monthly_sip.empty:
            monthly_sip_plot = monthly_sip.copy()
            monthly_sip_plot["month"] = pd.to_datetime(monthly_sip_plot["month"])
            fig_sip = px.line(
                monthly_sip_plot,
                x="month",
                y="sip_inflow_crore",
                title="Monthly SIP Capital Inflow Trend (2022 – 2025)",
                labels={"sip_inflow_crore": "SIP Inflow (₹ Crores)", "month": "Month"},
                markers=True,
                color_discrete_sequence=["#38BDF8"]
            )
            fig_sip.update_layout(
                template="plotly_white",
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            fig_sip.update_traces(line=dict(width=3), marker=dict(size=6, color="#0284C7"))
            st.plotly_chart(fig_sip, use_container_width=True)

    with col_chart2:
        if not scorecard_df.empty:
            cat_counts = scorecard_df["category"].value_counts().reset_index()
            cat_counts.columns = ["category", "count"]
            fig_cat = px.pie(
                cat_counts,
                names="category",
                values="count",
                title="Mutual Fund Category Distribution",
                hole=0.45,
                color_discrete_sequence=PASTEL_PALETTE
            )
            fig_cat.update_layout(
                template="plotly_white",
                height=380,
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_cat, use_container_width=True)


# ==============================================================================
# 2. Fund Scorecard & Explorer View
# ==============================================================================
elif nav_selection == "Fund Scorecard & Explorer":
    st.markdown("#### 🏆 Fund Performance Scorecard (0–100 Rating Scale)")

    if not scorecard_df.empty:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            selected_amc = st.multiselect("Filter by Fund House (AMC)", options=sorted(scorecard_df["fund_house"].dropna().unique()))
        with col_f2:
            selected_cat = st.multiselect("Filter by Category", options=sorted(scorecard_df["category"].dropna().unique()))
        with col_f3:
            min_score = st.slider("Minimum Composite Score (0–100)", 0, 100, 40)

        df_filtered = scorecard_df[scorecard_df["scorecard_score"] >= min_score].copy()
        if selected_amc:
            df_filtered = df_filtered[df_filtered["fund_house"].isin(selected_amc)]
        if selected_cat:
            df_filtered = df_filtered[df_filtered["category"].isin(selected_cat)]

        st.dataframe(
            df_filtered[[
                "fund_rank", "amfi_code", "scheme_name", "fund_house", "category", 
                "scorecard_score", "cagr_3yr_pct", "sharpe_ratio", "sortino_ratio", 
                "alpha_pct", "beta", "expense_ratio_pct", "max_drawdown_pct"
            ]],
            use_container_width=True,
            hide_index=True
        )

        st.markdown("<br>", unsafe_allow_html=True)
        top10_bar = df_filtered.head(10).copy()
        fig_bar = px.bar(
            top10_bar,
            x="scorecard_score",
            y="scheme_name",
            orientation="h",
            color="scorecard_score",
            color_continuous_scale=["#BAE6FD", "#60A5FA", "#3B82F6", "#1D4ED8"],
            title="Top Filtered Funds by Scorecard Score",
            labels={"scorecard_score": "Composite Score (0–100)", "scheme_name": "Scheme"}
        )
        fig_bar.update_layout(
            template="plotly_white",
            yaxis=dict(autorange="reversed"),
            height=420,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_bar, use_container_width=True)


# ==============================================================================
# 3. Risk & Return Analytics View
# ==============================================================================
elif nav_selection == "Risk & Return Analytics":
    st.markdown("#### ⚡ Risk & Return Quantitative Modeling")

    if not scorecard_df.empty:
        plot_df = scorecard_df.copy()
        
        # Ensure bubble sizes are strictly positive floats to prevent scatter size errors
        plot_df["bubble_size"] = plot_df["scorecard_score"].fillna(50).clip(lower=10, upper=100)

        t1, t2 = st.tabs(["📊 3-Yr CAGR vs Sharpe Ratio", "📈 Alpha vs Beta Risk Profile"])

        with t1:
            fig_scatter1 = px.scatter(
                plot_df,
                x="sharpe_ratio",
                y="cagr_3yr_pct",
                color="category",
                size="bubble_size",
                hover_name="scheme_name",
                title="3-Year CAGR Return (%) vs Sharpe Ratio Risk Profile",
                labels={"sharpe_ratio": "Sharpe Ratio (Total Risk-Adjusted Return)", "cagr_3yr_pct": "3-Year CAGR Return (%)"},
                template="plotly_white",
                color_discrete_sequence=PASTEL_PALETTE
            )
            fig_scatter1.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=450
            )
            st.plotly_chart(fig_scatter1, use_container_width=True)

        with t2:
            fig_scatter2 = px.scatter(
                plot_df,
                x="beta",
                y="alpha_pct",
                color="fund_house",
                size="bubble_size",
                hover_name="scheme_name",
                title="Alpha vs Beta Risk Profile (OLS Regression against Nifty 100)",
                labels={"beta": "Beta (Market Sensitivity)", "alpha_pct": "Annualized Alpha (%)"},
                template="plotly_white",
                color_discrete_sequence=PASTEL_PALETTE
            )
            fig_scatter2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=450
            )
            st.plotly_chart(fig_scatter2, use_container_width=True)

    if not var_df.empty:
        st.markdown("---")
        st.markdown("#### 📉 Historical 95% Value at Risk (VaR) & Conditional VaR (CVaR)")
        st.dataframe(var_df.head(10), use_container_width=True, hide_index=True)


# ==============================================================================
# 4. SIP Calculator View
# ==============================================================================
elif nav_selection == "SIP Calculator":
    st.markdown("#### 🧮 Interactive SIP Future Value Calculator")

    col_s1, col_s2 = st.columns([1, 2])

    with col_s1:
        monthly_amount = st.number_input("Monthly SIP Amount (INR)", min_value=500, max_value=500000, value=10000, step=500)
        tenure_years = st.slider("Investment Tenure (Years)", min_value=1, max_value=30, value=10)
        expected_cagr = st.slider("Expected Annual CAGR Return (%)", min_value=4.0, max_value=30.0, value=15.0, step=0.5)

        # SIP Future Value Formula: P * [((1+i)^n - 1) / i] * (1+i)
        months = tenure_years * 12
        monthly_rate = (expected_cagr / 100) / 12
        future_val = monthly_amount * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        total_invested = monthly_amount * months
        wealth_gain = future_val - total_invested

    with col_s2:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border:1px solid #BBF7D0; padding:20px; border-radius:14px; margin-bottom:18px;">
            <div style="font-size:0.9rem; color:#166534; font-weight:700; text-transform:uppercase;">Projected Corpus at Maturity</div>
            <div style="font-size:2.1rem; font-weight:800; color:#14532D; margin:4px 0;">₹{future_val:,.0f}</div>
            <div style="font-size:0.95rem; color:#15803D;">
                Total Capital Invested: <b>₹{total_invested:,.0f}</b> &nbsp;|&nbsp; Estimated Wealth Gain: <b>₹{wealth_gain:,.0f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Year-by-year trajectory chart
        yearly_data = []
        for yr in range(1, tenure_years + 1):
            m = yr * 12
            fv = monthly_amount * (((1 + monthly_rate) ** m - 1) / monthly_rate) * (1 + monthly_rate)
            inv = monthly_amount * m
            yearly_data.append({"Year": f"Yr {yr}", "Total Invested": inv, "Estimated Future Value": fv})

        df_sip_chart = pd.DataFrame(yearly_data)
        fig_sip_proj = px.bar(
            df_sip_chart,
            x="Year",
            y=["Total Invested", "Estimated Future Value"],
            barmode="group",
            title=f"Wealth Growth Trajectory ({tenure_years} Years @ {expected_cagr}% CAGR)",
            labels={"value": "Amount (INR)", "variable": "Breakdown"},
            template="plotly_white",
            color_discrete_map={"Total Invested": "#94A3B8", "Estimated Future Value": "#34D399"}
        )
        fig_sip_proj.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_sip_proj, use_container_width=True)


# ==============================================================================
# 5. Smart Fund Recommender View
# ==============================================================================
elif nav_selection == "Smart Fund Recommender":
    st.markdown("#### 🤖 Smart Mutual Fund Recommender Engine")
    st.markdown("Select your risk profile to view top-ranked funds filtered by Sharpe ratio and downside resilience.")

    col_r1, col_r2 = st.columns([1, 3])

    with col_r1:
        risk_input = st.selectbox("Select Your Risk Appetite", ["Low", "Moderate", "High"], index=1)
        top_k = st.slider("Number of Recommendations", 1, 5, 3)
        btn_rec = st.button("Generate Recommendations", type="primary")

    with col_r2:
        if btn_rec or True:
            if recommend_funds is not None:
                recs = recommend_funds(risk_appetite=risk_input, top_n=top_k)
                st.markdown(f"##### Recommended Top {top_k} Funds for [{risk_input.upper()}] Risk Appetite")

                for idx, row in recs.iterrows():
                    cagr_val = f"{row['cagr_3yr_pct']:.2f}%" if "cagr_3yr_pct" in row and pd.notna(row["cagr_3yr_pct"]) else "N/A"
                    sharpe_val = f"{row['sharpe_ratio']:.2f}" if "sharpe_ratio" in row and pd.notna(row["sharpe_ratio"]) else "N/A"
                    alpha_val = f"{row['alpha_pct']:.2f}%" if "alpha_pct" in row and pd.notna(row["alpha_pct"]) else "N/A"
                    beta_val = f"{row['beta']:.2f}" if "beta" in row and pd.notna(row["beta"]) else "N/A"
                    expense_val = f"{row['expense_ratio_pct']:.2f}%" if "expense_ratio_pct" in row and pd.notna(row["expense_ratio_pct"]) else "N/A"
                    score_txt = f" | Score: <b>{row['scorecard_score']:.1f}/100</b>" if "scorecard_score" in row and pd.notna(row["scorecard_score"]) else ""
                    scheme_name = row.get("scheme_name", "Scheme")
                    amfi_code = row.get("amfi_code", "")
                    fund_house = row.get("fund_house", "Fund House")
                    category = row.get("category", "Mutual Fund")
                    risk_cat = row.get("risk_category", row.get("risk_grade", "Moderate"))

                    st.markdown(f"""
                    <div class="pastel-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="color:#1E293B; margin:0; font-size:1.1rem;">Rank #{idx}: {scheme_name} ({amfi_code})</h4>
                            <span class="metric-badge badge-blue">{category}</span>
                        </div>
                        <p style="color:#64748B; font-size:0.88rem; margin:6px 0 10px 0;">Fund House: <b>{fund_house}</b> | Risk Grade: <b>{risk_cat}</b></p>
                        <div style="display:flex; gap:18px; flex-wrap:wrap; font-size:0.92rem; color:#0F172A;">
                            <span>3-Yr CAGR: <b style="color:#16A34A;">{cagr_val}</b></span>
                            <span>Sharpe: <b>{sharpe_val}</b></span>
                            <span>Alpha: <b>{alpha_val}</b></span>
                            <span>Beta: <b>{beta_val}</b></span>
                            <span>Expense: <b>{expense_val}</b></span>
                            <span>{score_txt}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("Recommender module unavailable.")
