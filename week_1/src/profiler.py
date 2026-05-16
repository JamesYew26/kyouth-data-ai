import sqlite3
import os


def run_data_profile(db_path=os.path.join("3_gold", "jobs.db")):
    # If the jobs.db file specifically doesn't exist, handle gracefully
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 1. Total Records
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_records = cursor.fetchone()[0]

        # 2. Null Counts
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN job_title IS NULL THEN 1 ELSE 0 END) as null_title,
                SUM(CASE WHEN company IS NULL THEN 1 ELSE 0 END) as null_company,
                SUM(CASE WHEN description IS NULL THEN 1 ELSE 0 END) as null_desc
            FROM jobs
        """)
        nulls = cursor.fetchone()

        # 3. Average Description Length
        cursor.execute("SELECT AVG(LENGTH(description)) FROM jobs")
        avg_len = int(cursor.fetchone()[0] or 0)

        # 4. Shortest Description
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs 
            WHERE description IS NOT NULL
            ORDER BY len ASC LIMIT 1
        """)
        short = cursor.fetchone()

        # 5. Longest Description
        cursor.execute("""
            SELECT LENGTH(description) as len, source_id, job_title 
            FROM jobs 
            WHERE description IS NOT NULL
            ORDER BY len DESC LIMIT 1
        """)
        long = cursor.fetchone()

        # Final Report Output
        print("--- 🔍 DATA QUALITY REPORT ---")
        print(f"📈 Total Records: {total_records}")
        print(f"❓ Missing Values -> job_title: {nulls['null_title']}, company: {nulls['null_company']}, description: {nulls['null_desc']}")
        print(f"📝 Avg Description Length: {avg_len} chars")
        print(f"⚠️ Shortest Description: {short['len']} chars")
        print(f"   ↳ source_id: {short['source_id']} | job_title: {short['job_title']}")
        print(f"🚨 Longest Description: {long['len']} chars")
        print(f"   ↳ source_id: {long['source_id']} | job_title: {long['job_title']}")

    except Exception as e:
        print(f"An error occurred during profiling: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
