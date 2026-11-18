"""CLI orchestrator for the JobStreet medallion pipeline.

uv run main.py ingest | process | load | profile | all
"""

import argparse
import logging
from pathlib import Path

from src.ingestor import ingest_all_mhtml
from src.loader import load_all_jsons
from src.processor import process_all_html
from src.profiler import run_data_profile

# Resolve paths from this file, not the current working directory,
# so the pipeline behaves the same no matter where it is launched from.
DATA_DIR = Path(__file__).resolve().parent / "data"
SOURCE_DIR = DATA_DIR / "0_source"
BRONZE_DIR = DATA_DIR / "1_bronze"
SILVER_DIR = DATA_DIR / "2_silver"
GOLD_DB = DATA_DIR / "3_gold" / "jobs.db"

STAGES = {
    "ingest": lambda: ingest_all_mhtml(SOURCE_DIR, BRONZE_DIR),
    "process": lambda: process_all_html(BRONZE_DIR, SILVER_DIR),
    "load": lambda: load_all_jsons(SILVER_DIR, GOLD_DB),
    "profile": lambda: run_data_profile(GOLD_DB),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="JobStreet medallion pipeline")
    parser.add_argument(
        "command",
        choices=[*STAGES, "all"],
        help="stage to run; 'all' runs ingest -> process -> load -> profile",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="per-file logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    for name in STAGES if args.command == "all" else [args.command]:
        logging.getLogger("pipeline").info("Running stage: %s", name)
        STAGES[name]()


if __name__ == "__main__":
    main()
