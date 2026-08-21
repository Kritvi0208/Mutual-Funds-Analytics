"""
recommender.py - Rule-Based Mutual Fund Recommender Engine
"""
from scripts.recommender import recommend_funds

if __name__ == "__main__":
    import sys
    risk_input = sys.argv[1] if len(sys.argv) > 1 else "Moderate"
    print(f"--- RECOMMENDATIONS FOR RISK PROFILE [{risk_input}] ---")
    print(recommend_funds(risk_input, 3))
