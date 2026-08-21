"""
run_pipeline.py - Master Pipeline Execution Script for Mutual Funds Analytics

Runs the complete end-to-end data pipeline sequentially:
1. Live NAV API Ingestion (scripts/live_nav_fetch.py)
2. Master ETL Pipeline & Schema Validation (scripts/etl_pipeline.py)
3. Performance & Risk Analytics Engine (scripts/compute_metrics.py)
4. Exploratory Data Analysis & Visualizations (scripts/generate_eda.py)
5. Advanced Risk Analytics & Recommender (scripts/generate_advanced.py)
6. Power BI Dashboard & Visual Exporter (scripts/generate_powerbi_dashboard.py)
7. PowerPoint Presentation Generator (scripts/generate_presentation.py)
8. Final Capstone PDF Report Generator (scripts/generate_final_pdf.py)

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
SCRIPTS_DIR = BASE_DIR / "scripts"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("MasterPipeline")

PIPELINE_STEPS = [
    ("1/8: Live NAV API Ingestion", "live_nav_fetch.py"),
    ("2/8: Master ETL Pipeline & Database Loader", "etl_pipeline.py"),
    ("3/8: Performance & Risk Analytics Engine", "compute_metrics.py"),
    ("4/8: Exploratory Data Analysis & Figures", "generate_eda.py"),
    ("5/8: Advanced Risk Analytics & Recommender", "generate_advanced.py"),
    ("6/8: Power BI Dashboard & Page Exporter", "generate_powerbi_dashboard.py"),
    ("7/8: PowerPoint Presentation Generator", "generate_presentation.py"),
    ("8/8: Final PDF Capstone Report Generator", "generate_final_pdf.py")
]


def run_pipeline():
    """Run all pipeline scripts sequentially."""
    logger.info("=================================================================")
    logger.info(" STARTING MASTER MUTUAL FUNDS ANALYTICS PIPELINE EXECUTION")
    logger.info("=================================================================")

    for step_num, script_name in PIPELINE_STEPS:
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            logger.error(f"Script {script_name} missing at {script_path}. Skipping.")
            continue

        logger.info(f"Executing Step [{step_num}] -> scripts/{script_name}...")
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
