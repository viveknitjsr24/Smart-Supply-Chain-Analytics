"""
main.py
-------
Runs the entire Smart Supply Chain Analytics pipeline end-to-end, in order.

Usage:
    pip install -r requirements.txt
    python main.py

This regenerates everything from scratch: synthetic raw data -> cleaned data
-> EDA charts -> demand forecasts -> inventory optimization -> warehouse
optimization -> SQLite database + validated SQL queries.

Random seeds are fixed throughout, so re-running this script reproduces
identical results every time.
"""

import subprocess
import sys
import time

STEPS = [
    ("Phase 2/3 - Generating synthetic dataset", "src/generate_data.py"),
    ("Phase 3 - Cleaning data", "src/data_cleaning.py"),
    ("Phase 4 - Running EDA", "src/eda.py"),
    ("Phase 5 - Demand forecasting", "src/forecasting.py"),
    ("Phase 6 - Inventory optimization", "src/inventory.py"),
    ("Phase 7 - Warehouse optimization", "src/warehouse.py"),
    ("Phase 8 - Building SQL database & validating queries", "sql/load_data_and_test_queries.py"),
]

def run_pipeline():
    start = time.time()
    for label, script in STEPS:
        print("\n" + "=" * 70)
        print(label)
        print("=" * 70)
        result = subprocess.run([sys.executable, script])
        if result.returncode != 0:
            print(f"\nPipeline stopped: {script} failed.")
            sys.exit(1)
    print(f"\nPipeline complete in {time.time() - start:.1f} seconds.")
    print("Outputs are in data/processed/, images/, and sql/supply_chain.db")
    print("Import dashboard/powerbi_data/*.csv into Power BI Desktop to build the dashboard.")

if __name__ == "__main__":
    run_pipeline()
