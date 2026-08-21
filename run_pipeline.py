"""
run_pipeline.py - Master Pipeline Execution Script for Mutual Funds Analytics

Runs the complete end-to-end data pipeline sequentially:
1. Data Ingestion & Schema Validation (data_ingestion.py)
2. Live NAV API Ingestion (live_nav_fetch.py)
3. Data Cleaning & Normalization (data_cleaner.py)
4. SQLite Star Schema Database Loader (data_loader.py)
5. Exploratory Data Analysis & Visualizations (generate_eda.py)
6. Performance & Risk Analytics Engine (generate_performance.py)
7. Advanced Risk Modeling & Recommender (generate_advanced.py)
8. Presentation Deck Generator (generate_presentation.py)
9. Final PDF Report Generator (generate_final_pdf.py)

Usage:
    python run_pipeline.py
"""

import sys
import logging
import subprocess
from pathlib import Path

# Enforce UTF-8 standard output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MasterPipeline")

PIPELINE_STEPS = [
    ("1/10: Data Ingestion & Schema Validation", "data_ingestion.py"),
    ("2/10: Live NAV API Ingestion", "live_nav_fetch.py"),
    ("3/10: Data Cleaning & Normalization", "data_cleaner.py"),
    ("4/10: SQLite Star Schema Database Loader", "data_loader.py"),
    ("5/10: Exploratory Data Analysis & Figures", "generate_eda.py"),
    ("6/10: Performance & Risk Analytics Engine", "generate_performance.py"),
    ("7/10: Advanced Risk Analytics & Recommender", "generate_advanced.py"),
    ("8/10: Power BI Dashboard & Page Exporter", "generate_powerbi_dashboard.py"),
    ("9/10: PowerPoint Presentation Generator", "generate_presentation.py"),
    ("10/10: Final PDF Capstone Report Generator", "generate_final_pdf.py")
]


def run_pipeline():
    """Run all pipeline scripts sequentially."""
    logger.info("=================================================================")
    logger.info(" STARTING MASTER MUTUAL FUNDS ANALYTICS PIPELINE EXECUTION")
    logger.info("=================================================================")

    for step_num, script_name in PIPELINE_STEPS:
        script_path = BASE_DIR / script_name
        if not script_path.exists():
            logger.error(f"Script {script_name} missing at {script_path}. Skipping.")
            continue

        logger.info(f"Executing Step [{step_num}] -> {script_name}...")
        res = subprocess.run([sys.executable, str(script_path)], cwd=str(BASE_DIR))

        if res.returncode != 0:
            logger.error(f"Step [{step_num}] failed with exit code {res.returncode}.")
            sys.exit(res.returncode)

        logger.info(f"Step [{step_num}] completed successfully.")

    logger.info("=================================================================")
    logger.info(" [SUCCESS] MASTER PIPELINE EXECUTION COMPLETED WITHOUT ERRORS!")
    logger.info("=================================================================")


if __name__ == "__main__":
    run_pipeline()
