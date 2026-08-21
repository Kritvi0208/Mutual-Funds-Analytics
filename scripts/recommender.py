"""
scripts/recommender.py - Rule-Based Mutual Fund Recommender Engine
"""
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PROC_DIR = BASE_DIR / "data" / "processed"
TABLES_DIR = BASE_DIR / "reports" / "tables"

def recommend_funds(risk_appetite="Moderate", top_n=3):
    scorecard_path = TABLES_DIR / "fund_scorecard.csv"
    master_path = PROC_DIR / "01_fund_master.csv"
    
    if scorecard_path.exists():
        df = pd.read_csv(scorecard_path)
    else:
        df = pd.read_csv(PROC_DIR / "07_scheme_performance.csv")
        if "return_3yr_pct" in df.columns and "cagr_3yr_pct" not in df.columns:
            df["cagr_3yr_pct"] = df["return_3yr_pct"]
        if "alpha" in df.columns and "alpha_pct" not in df.columns:
            df["alpha_pct"] = df["alpha"]

    # Merge with fund master for risk_category if available
    if master_path.exists():
        master_df = pd.read_csv(master_path)
        if "risk_category" in master_df.columns:
            cols_to_merge = ["amfi_code", "risk_category"]
            if "risk_category" not in df.columns:
                df = df.merge(master_df[cols_to_merge], on="amfi_code", how="left")

    if "risk_category" not in df.columns:
        df["risk_category"] = df.get("risk_grade", "Moderate")

    risk_clean = str(risk_appetite).strip().capitalize()
    risk_mapping = {
        "Low": ["Low", "Low to Moderate", "Moderate"],
        "Moderate": ["Moderate", "Moderately High", "Moderate to High", "Equity", "Large Cap"],
        "High": ["High", "Very High", "Moderately High", "Small Cap", "Mid Cap", "Flexicap"]
    }
    allowed = risk_mapping.get(risk_clean, risk_mapping["Moderate"])
    
    filtered = df[df["risk_category"].astype(str).str.strip().isin(allowed)].copy()
    if filtered.empty:
        filtered = df.copy()

    sort_cols = [c for c in ["sharpe_ratio", "scorecard_score", "cagr_3yr_pct"] if c in filtered.columns]
    res = filtered.sort_values(by=sort_cols, ascending=False).head(top_n).reset_index(drop=True)
    res.index = res.index + 1
    return res

if __name__ == "__main__":
    risk_input = sys.argv[1] if len(sys.argv) > 1 else "Moderate"
    print(f"--- RECOMMENDATIONS FOR RISK PROFILE [{risk_input}] ---")
    print(recommend_funds(risk_input, 3))
