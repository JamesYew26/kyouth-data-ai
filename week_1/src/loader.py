import sqlite3
import json
import os
from pathlib import Path


def load_all_jsons(input_dir, output_dir):
    """
    Reads all JSON files from input_dir and loads them into a SQLite DB 
    located in output_dir.
    """
    input_path = Path(input_dir)
    db_dir = Path(output_dir)
    db_path = db_dir / "jobs.db"

    # Counters for the summary
    total_processed = 0
    inserted_count = 0
    skipped_count = 0

    db_dir.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            source_id TEXT UNIQUE NOT NULL,
            job_title TEXT,
            company TEXT,
            description TEXT,
            tech_stack TEXT,
            loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    if not input_path.exists():
        print(f"❌ Error: Input directory {input_dir} does not exist.")
        return

    json_files = [f for f in os.listdir(input_path) if f.endswith('.json')]
    
    if not json_files:
        print(f"⚠️ No JSON files found in {input_dir}")
        return

    for file_name in json_files:
        file_full_path = input_path / file_name
        
        try:
            with open(file_full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = data if isinstance(data, list) else [data]
            
            for record in records:
                total_processed += 1 # Increment total for every record found
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO jobs (source_id, job_title, company, description, tech_stack)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            record.get("source_id"), 
                            record.get("job_title"), 
                            record.get("company"), 
                            record.get("description"),
                            record.get("tech_stack")
                        ),
                    )
                    
                    if cursor.rowcount > 0:
                        print(f"✅ Inserted: {file_name}")
                        inserted_count += 1
                    else:
                        print(f"⏩ Skipped (duplicate): {file_name}")
                        skipped_count += 1
                        
                except Exception as e:
                    print(f"  ❌ Failed record in {file_name}: {e}")

        except Exception as e:
            print(f"❌ Error reading file {file_name}: {e}")

    connection.commit()
    connection.close()

    # Final Summary Output
    print("\n")
    print("📊 Gold Summary:")
    print(f"Total: {total_processed} | Inserted: {inserted_count} | Skipped: {skipped_count}")
