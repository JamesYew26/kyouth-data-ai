import sqlite3
import os

def run_data_profile(db_path="jobs.db"):
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 1. Total Records
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_records = cursor.fetchone()[0]

        # 2. Null Counts
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN job_title IS NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN company IS NULL THEN 1 ELSE 0 END),
                SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END)
            FROM jobs
        """)
        nulls = cursor.fetchone()

        # 3. Description Length Metrics
        cursor.execute("SELECT AVG(LENGTH(description)) FROM jobs")
        avg_len = int(cursor.fetchone()[0] or 0)

        # 4. Shortest Description
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs ORDER BY len ASC LIMIT 1
        """)
        short = cursor.fetchone()

        # 5. Longest Description
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs ORDER BY len DESC LIMIT 1
        """)
        long = cursor.fetchone()

        # Output Report
        print("--- 🔍 DATA QUALITY REPORT ---")
        print(f"📈 Total Records: {total_records}")
        print(f"❓ Missing Values -> job_title: {nulls[0]}, company: {nulls[1]}, description: {nulls[2]}")
        print(f"📝 Avg Description Length: {avg_len} chars")
        print(f"⚠️ Shortest Description: {short[0]} chars")
        print(f"   ↳ source_id: {short[1]} | job_title: {short[2]}")
        print(f"🚨 Longest Description: {long[0]} chars")
        print(f"   ↳ source_id: {long[1]} | job_title: {long[2]}")

    except Exception as e:
        print(f"Error during profiling: {e}")
    finally:
        conn.close()