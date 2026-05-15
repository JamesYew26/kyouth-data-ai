import argparse
from pathlib import Path # Figure out why use Path?
from src.ingestor import ingest_all_mhtml
from src.processor import process_all_html
# from src.loader import load_all_jsons
# from src.run_data_profile import run_data_profile

SOURCE_DIR = Path("data/0_source")
BRONZE_DIR = Path("data/1_bronze")
SILVER_DIR = Path("data/2_silver")
GOLD_DIR = Path("data/3_gold")
DB_NAME = "jobs.db"

# def run_profiler():
#     db_path = GOLD_DIR/DB_NAME
#     run_data_profile(db_path)

def run_gold():
    print("🥇 Gold:...")
    input_dir = SILVER_DIR
    output_dir = GOLD_DIR
    load_all_jsons(input_dir, output_dir)

def run_silver():
    print("🥈 Silver:...")
    input_dir = BRONZE_DIR
    output_dir = SILVER_DIR
    process_all_html(input_dir, output_dir)


def run_bronze():
    print("🥉 Bronze:...")
    input_dir = SOURCE_DIR
    output_dir = BRONZE_DIR
    ingest_all_mhtml(input_dir, output_dir)
    
def main():
	# ORCHESTRATION TO BE IMPLEMENTED HERE
    # 1. Setup the Argument Parser
    parser = argparse.ArgumentParser(description="Job Data Pipeline CLI")
    
    # 2. Add subparsers to handle different commands
    subparsers = parser.add_subparsers(dest="command", help="Available pipeline stages")

    # Command: ingest
    subparsers.add_parser("ingest", help="Run the ingestion (Bronze) stage")
    
    # Command: process
    subparsers.add_parser("process", help="Run the processing (Silver) stage")

    # Command: load
    subparsers.add_parser("load", help="Run the loading (Gold) stage")

    # Command: profile
    subparsers.add_parser("profile", help="Run the data profiling stage")

    # 3. Parse the arguments from the terminal
    args = parser.parse_args()

    # 4. Routing Logic
    if args.command == "ingest":
        run_bronze()
    elif args.command == "process":
        run_silver()
    # elif args.command == "load":
    #     run_gold()
    # elif args.command == "profile":
    #     run_profiler()
    else:
        # If the user just types 'python3 main.py' without a command
        parser.print_help()

if __name__ == "__main__":
    main()