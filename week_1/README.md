# JobStreet Data Pipeline

A robust ETL (Extract, Transform, Load) pipeline designed to scrape job listings from MHTML snapshots and transform them into structured analytical data. This project implements a **Medallion Architecture** to ensure data lineage, integrity, and scalability.

---

## Project Description
The goal of this project is to automate the extraction of job market data from semi-structured web snapshots. By transitioning data through multiple stages—from raw MHTML to a structured SQLite database—this pipeline provides a reliable way to analyze job trends, salaries, and company requirements without the fragility of live web scraping.

---

## Project Structure
The following folder structure is strictly adhered to for data lineage and modularity:

```text
week1/
├── data/
│   ├── 0_source/          # Vendor Data: Unedited MHTML snapshots
│   ├── 1_bronze/          # Raw Data: Decoded HTML files
│   ├── 2_silver/          # Clean Data: Validated JSON records
│   └── 3_gold/            # Final Warehouse: SQLite Database (jobs.db)
├── src/
│   ├── ingestor.py        # Day 1: Extracts 0_source -> 1_bronze
│   ├── processor.py       # Day 2: Cleans/Validates 1_bronze -> 2_silver
│   ├── loader.py          # Day 3: Loads 2_silver -> 3_gold
│   └── profiler.py        # Day 4: Quality checks on Gold layer
├── main.py                # CLI Orchestrator (The Conductor)
├── pyproject.toml         # Environment & Dependencies
├── uv.lock                # Deterministic lockfile
└── README.md              # Technical Manual

git clone <your-repo-url>
cd week1

# Create the version file
    echo "3.14" > .python-version
    # Install the specific Python version and initialize environment
    uv python install
    uv venv
    ```
  **Activate Virtual Environment:**
    *   **macOS/Linux:** `source .venv/bin/activate`
    *   **Windows:** `.venv\Scripts\activate`
  **Install Dependencies:**
    ```bash
    uv add bs4 ruff pydantic
    ```

### `uv` Package Manager Cheat Sheet
| Action | Command |
| :--- | :--- |
| **Add a package** | `uv add <package_name>` |
| **Remove a package** | `uv remove <package_name>` |
| **Run the orchestrator** | `uv run main.py <command>` |
| **Lint/Format code** | `uv run ruff check .` |
| **Sync environment** | `uv sync` |

---

## Usage
The pipeline is managed via `main.py`. Ensure your MHTML files are placed in `data/0_source/` before starting.

### Step 1: Ingest (Bronze)
Decodes MHTML files into raw HTML.
```bash
uv run python main.py ingest
uv run python main.py process
uv run python main.py load
uv run python main.py profile
uv run python main.py all

Technical Reflections
Module 1: The Extractor (Medallion & Lakehouses)
Reflection:
Keeping original raw HTML files in the Bronze layer acts as a "source of truth." In industry, requirements shift constantly; if we decide to extract a new field (like "Years of Experience") months later, we can simply re-process the Bronze files. Without them, we would have to re-scrape a live site that may have already removed the old job postings. It provides a safety net for debugging extraction logic without losing data.
ANS:

Module 2: Treatment Plant (ETL vs ELT & Scale)
Reflection:
Cloud systems prefer ELT (Load then Transform) because modern warehouses like Snowflake can scale compute instantly to handle heavy cleaning via SQL. In our local sequential Python script, processing one file at a time is a bottleneck. Distributed processing (like Spark) would allow us to parallelize these tasks, turning a linear wait time into a concurrent operation across multiple CPU cores or nodes.
ANS:

Module 3: The Blueprint & The Vault (Storage & Contracts)
Reflection:
If an essential field like job_title is missing, we fail early rather than inserting null into the DB. This prevents "silent data corruption," where business dashboards might display incorrect metrics without warning. Using INSERT OR IGNORE ensures the Gold layer is idempotent—running the pipeline multiple times won't create duplicate records, which is critical for maintaining a "clean room" warehouse.
ANS:

Module 4: The QA Inspector & Orchestrator (Orchestration & DAGs)
Reflection:
If processor.py crashes halfway through 1,000 files, a manual script requires human intervention to resume. Real-world tools like Airflow use Directed Acyclic Graphs (DAGs) to track state and dependencies. They provide automated retries and scheduling, ensuring the pipeline is self-healing and can recover from transient errors (like network blips or locked files) without manual oversight.
ANS: