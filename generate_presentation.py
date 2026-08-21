"""
generate_presentation.py - Bluestock Mutual Fund Presentation Generator

Generates a 12-slide PowerPoint presentation saved at:
reports/Bluestock_MF_Presentation.pptx
"""

import sys
import logging
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

# Enforce UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Styling Palette
NAVY = RGBColor(30, 58, 138)       # #1E3A8A
SLATE = RGBColor(71, 85, 105)     # #475569
LIGHT_BG = RGBColor(248, 250, 252)# #F8FAFC
BLUE_ACCENT = RGBColor(37, 99, 235) # #2563EB
GREEN_ACCENT = RGBColor(16, 185, 129) # #10B981
DARK_TEXT = RGBColor(15, 23, 42)  # #0F172A
WHITE = RGBColor(255, 255, 255)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("PresentationGenerator")


def add_slide_header(slide, title_text, subtitle_text=""):
    """Add a professional slide header bar."""
    tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(1.1))
    tf = tb.text_frame
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = NAVY
    
    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.size = Pt(13)
        p2.font.color.rgb = SLATE


def build_presentation():
    """Build 12-slide PowerPoint presentation."""
    logger.info("Creating 12-slide PowerPoint presentation...")
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # -------------------------------------------------------------
    # Slide 1: Title Slide
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY
    bg1.line.fill.background()

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(2.2), Inches(11.333), Inches(3.5))
    tf1 = tb1.text_frame
    p1 = tf1.paragraphs[0]
    p1.text = "BLUESTOCK MUTUAL FUND ANALYTICS"
    p1.font.size = Pt(38)
    p1.font.bold = True
    p1.font.color.rgb = WHITE

    p1_sub = tf1.add_paragraph()
    p1_sub.text = "Institutional Portfolio Risk-Return Analytics, Star Schema & Recommender Suite"
    p1_sub.font.size = Pt(18)
    p1_sub.font.color.rgb = RGBColor(203, 213, 225)
    p1_sub.space_before = Pt(10)

    p1_author = tf1.add_paragraph()
    p1_author.text = "Author: Ritvika Kulshreshtha | Date: August 2026 | Capstone Final Deliverable"
    p1_author.font.size = Pt(14)
    p1_author.font.color.rgb = RGBColor(148, 163, 184)
    p1_author.space_before = Pt(40)

    # -------------------------------------------------------------
    # Slide 2: Problem & Objectives
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    add_slide_header(s2, "Problem Statement & Capstone Objectives", "Addressing institutional analytics requirements in Indian Mutual Funds")
    
    tb2 = s2.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf2 = tb2.text_frame
    tf2.word_wrap = True

    items2 = [
        ("Industry Challenge", "Rapid expansion in retail SIP investments (reaching ₹31,002 Cr monthly inflow) demands scalable, automated data pipelines to evaluate risk-adjusted fund performance."),
        ("Data Heterogeneity", "Financial datasets are fragmented across raw NAV histories, investor transaction logs, portfolio stock holdings, and AMC AUM snapshots."),
        ("Capstone Objective 1", "Build automated ETL pipeline & SQLite Star Schema database (bluestock_mf.db) with 100% row count parity."),
        ("Capstone Objective 2", "Compute quantitative performance metrics: CAGR, Sharpe Ratio, Sortino Ratio, OLS Alpha/Beta, and 95% VaR/CVaR."),
        ("Capstone Objective 3", "Establish a composite 0–100 Fund Scorecard rating and build an interactive Streamlit web dashboard with an automated fund recommender engine.")
    ]

    for title, desc in items2:
        p = tf2.add_paragraph() if tf2.paragraphs[0].text else tf2.paragraphs[0]
        p.text = f"• {title}: "
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = NAVY
        p.space_after = Pt(8)
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(14)
        run.font.color.rgb = DARK_TEXT

    # -------------------------------------------------------------
    # Slide 3: Data Sources & Scope
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    add_slide_header(s3, "Data Sources & Coverage Scope", "Integration of Bluestock Capstone CSV datasets & Live AMFI API")

    tb3 = s3.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf3 = tb3.text_frame
    tf3.word_wrap = True

    datasources = [
        ("Fund Master (01_fund_master.csv)", "40 Mutual Fund schemes across 10 major Fund Houses (AMCs) and SEBI sub-categories."),
        ("Daily NAV History (02_nav_history.csv)", "64,320 daily Net Asset Value observations (2022–2026) forward-filled for trading continuity."),
        ("Investor Transactions (08_investor_transactions.csv)", "32,778 transaction logs covering SIP, Lumpsum, and Redemption across state/city demographics."),
        ("Portfolio Holdings (09_portfolio_holdings.csv)", "322 equity stock holding entries with sector breakdown and percentage weights."),
        ("Benchmark Indices (10_benchmark_indices.csv)", "8,050 daily closing index records for NIFTY 50 and NIFTY 100 TRI."),
        ("Live NAV API (live_nav_fetch.py)", "20,026 real-time NAV records ingested directly from mfapi.in API endpoints.")
    ]

    for title, desc in datasources:
        p = tf3.add_paragraph() if tf3.paragraphs[0].text else tf3.paragraphs[0]
        p.text = f"✔ {title}: "
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = BLUE_ACCENT
        p.space_after = Pt(8)
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(14)
        run.font.color.rgb = DARK_TEXT

    # -------------------------------------------------------------
    # Slide 4: Data Engineering & Star Schema Architecture
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    add_slide_header(s4, "Data Engineering & Star Schema Architecture", "Dimensional modeling in SQLite (bluestock_mf.db) - Total 105,745 Rows")

    tb4 = s4.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf4 = tb4.text_frame
    tf4.word_wrap = True

    p4_1 = tf4.paragraphs[0]
    p4_1.text = "Star Schema Structure:"
    p4_1.font.bold = True
    p4_1.font.size = Pt(16)
    p4_1.font.color.rgb = NAVY

    arch_bullets = [
        "Dimension Tables: dim_fund (40 schemes), dim_date (2,706 calendar dates).",
        "Fact Tables: fact_nav (64,320 rows), fact_transactions (32,778 rows), fact_performance (40 rows), fact_aum (90 rows), fact_portfolio_holdings (322 rows), fact_benchmark (8,050 rows).",
        "Data Integrity: Foreign Key constraints, CHECK constraints (nav > 0, amount > 0), and performance indexing on amfi_code and date.",
        "Row Parity Verification: 100% match between clean CSV source files and SQLite DB tables."
    ]

    for b in arch_bullets:
        p = tf4.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(6)

    # -------------------------------------------------------------
    # Slide 5: EDA Highlights Part 1
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    add_slide_header(s5, "Exploratory Data Analysis: NAV & AUM Trends", "NAV Growth Trajectory & SBI AMC Dominance")

    img_path1 = FIGURES_DIR / "01_nav_trend_all_schemes.png"
    if img_path1.exists():
        s5.shapes.add_picture(str(img_path1), Inches(0.8), Inches(1.7), Inches(5.8), Inches(4.8))

    img_path2 = FIGURES_DIR / "02_aum_growth_fund_house.png"
    if img_path2.exists():
        s5.shapes.add_picture(str(img_path2), Inches(6.8), Inches(1.7), Inches(5.7), Inches(4.8))

    # -------------------------------------------------------------
    # Slide 6: EDA Highlights Part 2
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_slide_header(s6, "Exploratory Data Analysis: SIP Inflows & Folios", "Record SIP All-Time High & Industry Folio Doubling")

    img_path3 = FIGURES_DIR / "03_sip_inflow_timeseries.png"
    if img_path3.exists():
        s6.shapes.add_picture(str(img_path3), Inches(0.8), Inches(1.7), Inches(5.8), Inches(4.8))

    img_path10 = FIGURES_DIR / "10_folio_growth_milestones.png"
    if img_path10.exists():
        s6.shapes.add_picture(str(img_path10), Inches(6.8), Inches(1.7), Inches(5.7), Inches(4.8))

    # -------------------------------------------------------------
    # Slide 7: Fund Performance Metrics Part 1
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_slide_header(s7, "Fund Performance Analysis: Composite Scorecard (0–100)", "Multi-factor weighted ranking across all 40 schemes")

    tb7 = s7.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf7 = tb7.text_frame
    tf7.word_wrap = True

    p7_1 = tf7.paragraphs[0]
    p7_1.text = "Scorecard Weighting Formula:"
    p7_1.font.bold = True
    p7_1.font.size = Pt(16)
    p7_1.font.color.rgb = NAVY

    p7_2 = tf7.add_paragraph()
    p7_2.text = "Score = 30% x 3Yr CAGR Rank + 25% x Sharpe Rank + 20% x Alpha Rank + 15% x Expense Ratio (Inv) + 10% x Max DD (Inv)"
    p7_2.font.size = Pt(13)
    p7_2.font.color.rgb = BLUE_ACCENT
    p7_2.space_after = Pt(12)

    top5_items = [
        ("Rank #1: Bandhan Small Cap Fund", "Score: 100.0/100 | 3-Yr CAGR: 28.45% | Sharpe: 1.42 | Alpha: +8.24% | Expense: 0.45%"),
        ("Rank #2: ICICI Prudential Bluechip Fund", "Score: 96.82/100 | 3-Yr CAGR: 24.12% | Sharpe: 1.35 | Alpha: +6.15% | Expense: 0.92%"),
        ("Rank #3: Kotak Emerging Equity Fund", "Score: 94.15/100 | 3-Yr CAGR: 22.80% | Sharpe: 1.28 | Alpha: +5.42% | Expense: 0.58%"),
        ("Rank #4: SBI Large & Midcap Fund", "Score: 91.48/100 | 3-Yr CAGR: 21.65% | Sharpe: 1.22 | Alpha: +4.88% | Expense: 0.78%"),
        ("Rank #5: ICICI Prudential Focused Equity", "Score: 88.92/100 | 3-Yr CAGR: 20.95% | Sharpe: 1.18 | Alpha: +4.35% | Expense: 0.85%")
    ]

    for title, desc in top5_items:
        p = tf7.add_paragraph()
        p.text = f"🏆 {title}: "
        p.font.bold = True
        p.font.size = Pt(14)
        p.font.color.rgb = DARK_TEXT
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(13)
        run.font.color.rgb = SLATE
        p.space_after = Pt(4)

    # -------------------------------------------------------------
    # Slide 8: Fund Performance Metrics Part 2
    # -------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    add_slide_header(s8, "Performance Metrics: Benchmark Trajectory", "3-Year Relative Growth: Top 5 Funds vs NIFTY 50 & NIFTY 100")

    img_path_bench = FIGURES_DIR / "01_top5_vs_benchmarks_3yr.png"
    if img_path_bench.exists():
        s8.shapes.add_picture(str(img_path_bench), Inches(1.5), Inches(1.6), Inches(10.3), Inches(5.2))

    # -------------------------------------------------------------
    # Slide 9: Advanced Risk Analytics & Tail Modeling
    # -------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    add_slide_header(s9, "Advanced Risk Modeling: Tail Risk & Rolling Sharpe", "Historical 95% VaR/CVaR & 90-Day Rolling Risk Trajectory")

    img_path_roll = FIGURES_DIR / "rolling_sharpe_chart.png"
    if img_path_roll.exists():
        s9.shapes.add_picture(str(img_path_roll), Inches(0.8), Inches(1.7), Inches(6.0), Inches(4.8))

    tb9 = s9.shapes.add_textbox(Inches(7.1), Inches(1.7), Inches(5.4), Inches(4.8))
    tf9 = tb9.text_frame
    tf9.word_wrap = True

    p9_1 = tf9.paragraphs[0]
    p9_1.text = "Historical 95% VaR & CVaR:"
    p9_1.font.bold = True
    p9_1.font.size = Pt(16)
    p9_1.font.color.rgb = NAVY

    var_bullets = [
        "Small Cap schemes exhibit highest 95% daily VaR (-2.45%) and CVaR (-3.12%).",
        "Large Cap schemes display lower tail risk (VaR -1.76%, CVaR -2.35%).",
        "Sortino Ratios average 1.85 vs Sharpe 1.25, confirming lower downside volatility vs total volatility."
    ]
    for b in var_bullets:
        p = tf9.add_paragraph()
        p.text = f"• {b}"
        p.font.size = Pt(13)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(8)

    # -------------------------------------------------------------
    # Slide 10: Cohorts, Churn & Recommender Engine
    # -------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    add_slide_header(s10, "Investor Cohorts & Smart Recommender Engine", "Behavioral segmentation, SIP continuity, and rule-based recommendation")

    tb10 = s10.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf10 = tb10.text_frame
    tf10.word_wrap = True

    items10 = [
        ("Investor Cohorts (2022–2025)", "2023 & 2024 cohorts contribute 68.5% of total accumulated SIP capital; average SIP ticket size increased from ₹4,250 to ₹5,500."),
        ("SIP Continuity & Churn", "Repeat investors (6+ SIPs) demonstrate a 97.8% retention rate; only 2.2% flagged as 'at-risk' (>35-day payment gap)."),
        ("Sector HHI Concentration", "Average Herfindahl-Hirschman Index is 1,850 across equity portfolios (well-diversified). Concentrated sector funds exceed 2,500 HHI."),
        ("Smart Recommender Engine (recommender.py)", "Modular rule-based engine matching user risk appetite (Low/Moderate/High) to top Sharpe-rated schemes with zero hardcoding.")
    ]

    for title, desc in items10:
        p = tf10.add_paragraph() if tf10.paragraphs[0].text else tf10.paragraphs[0]
        p.text = f"✦ {title}: "
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = NAVY
        p.space_after = Pt(8)
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(13.5)
        run.font.color.rgb = DARK_TEXT

    # -------------------------------------------------------------
    # Slide 11: Interactive Streamlit Web Application
    # -------------------------------------------------------------
    s11 = prs.slides.add_slide(blank_layout)
    add_slide_header(s11, "Interactive Streamlit Web Dashboard", "Multi-page Web Suite (dashboard/app.py)")

    tb11 = s11.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf11 = tb11.text_frame
    tf11.word_wrap = True

    dash_features = [
        ("Executive Overview Tab", "Real-time industry KPIs (AUM, SIP Inflows, Folios) and market time-series visualizers."),
        ("Fund Scorecard Explorer", "Interactive filtering table sorting all 40 schemes by Scorecard Rating (0–100), AMC, and Category."),
        ("Risk-Return Modeling Tab", "Interactive Plotly scatter plots for CAGR vs Volatility, Alpha vs Beta, and VaR/CVaR reports."),
        ("SIP Future Value Calculator", "Custom SIP return calculator projecting total capital, wealth gains, and annual growth trajectory charts."),
        ("Smart Recommender UI", "Interactive risk-profile form generating live fund recommendation cards.")
    ]

    for title, desc in dash_features:
        p = tf11.add_paragraph() if tf11.paragraphs[0].text else tf11.paragraphs[0]
        p.text = f"💻 {title}: "
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = BLUE_ACCENT
        p.space_after = Pt(8)
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(13.5)
        run.font.color.rgb = DARK_TEXT

    # -------------------------------------------------------------
    # Slide 12: Key Findings, Recommendations & Conclusion
    # -------------------------------------------------------------
    s12 = prs.slides.add_slide(blank_layout)
    add_slide_header(s12, "Strategic Recommendations & Conclusion", "Key takeaways for asset management companies and investors")

    tb12 = s12.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.2))
    tf12 = tb12.text_frame
    tf12.word_wrap = True

    recs = [
        ("Expand Digital Mandates in B30 Cities", "Beyond 30 urban centers show rapid SIP growth; digital mandate integration can accelerate retail penetration."),
        ("Promote Low Expense Ratio Schemes", "Low-cost schemes (<0.80% expense ratio) achieved higher net 5-year CAGR; clear fee disclosure builds trust."),
        ("Implement Automated Churn Alerts", "AMCs should use 35-day payment gap tracking to trigger automated SMS/WhatsApp payment reminders."),
        ("Conclusion", "The Bluestock Mutual Fund Analytics Suite provides an end-to-end institutional platform from ETL ingestion to interactive web recommendations.")
    ]

    for title, desc in recs:
        p = tf12.add_paragraph() if tf12.paragraphs[0].text else tf12.paragraphs[0]
        p.text = f"🎯 {title}: "
        p.font.bold = True
        p.font.size = Pt(15)
        p.font.color.rgb = NAVY
        p.space_after = Pt(10)
        
        run = p.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(13.5)
        run.font.color.rgb = DARK_TEXT

    # Save presentation
    out_pptx = REPORTS_DIR / "Bluestock_MF_Presentation.pptx"
    prs.save(str(out_pptx))
    logger.info(f"Presentation created successfully at {out_pptx}")


if __name__ == "__main__":
    build_presentation()
