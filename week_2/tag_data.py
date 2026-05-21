# tag_data.py
import sqlite3
import time
from prompt_model import prompt_model  # 🔌 Connecting our two files

def tag_data(db_url: str):
    """
    Reads job descriptions from a SQLite database, uses Gemini via prompt_model.py
    to extract the technical stack, and updates the database safely in batches.
    """
    # 1. Connect to the database safely
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # 2. Fetch rows that are missing a tech_stack value
    try:
        query = "SELECT source_id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = '';"
        cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        conn.close()
        return

    # Configuration for batching and retries
    batch_size = 8
    retry_duration = 65
    model_name = 'gemini-2.5-flash'  # ✅ Correct official fast model identifier

    print(f"📋 Found {len(rows)} rows to process. Starting batch updates...")
    
    # 3. Loop through the data in batches
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        print(f"📦 Processing batch {batch_num} ({len(batch)} rows)...")
        
        success = False
        while not success:
            try:
                # Construct the prompt for this specific batch
                prompt = (
                    "Extract the technical stack (programming languages, frameworks, databases, tools) "
                    "used in each job description below. Respond using the format:\n"
                    "source_id: tech1, tech2, tech3\n\n"
                )
                
                for source_id, description in batch:
                    prompt += f"Source ID {source_id}:\n{description}\n\n"
                
                # Call the external Gemini module function
                print(f"🧠 Sending batch {batch_num} to Gemini...")
                llm_response = prompt_model(model_name, prompt)
                print(f"📥 Response received for batch {batch_num}.")
                
                # Parse the model's response line by line
                parsed_updates = []
                lines = llm_response.split('\n')
                
                for line in lines:
                    if ":" in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            source_id = int(parts[0].strip())
                            tech_stack = parts[1].strip()
                            parsed_updates.append((tech_stack, source_id))
                
                # 4. Save changes using a single batch update command
                if parsed_updates:
                    print(f"💾 Saving {len(parsed_updates)} updates to the database...")
                    update_query = "UPDATE jobs SET tech_stack = ? WHERE source_id = ?;"
                    cursor.executemany(update_query, parsed_updates)
                    conn.commit()
                
                success = True  # Batch completed successfully!
                print("💤 Pacing delay... waiting 12 seconds before the next batch.")
                time.sleep(12)  # 12 seconds * 5 rows per batch = perfectly spaced requests
                
            except Exception as e:
                # If ask_gemini fails, this block catches it and knows exactly which batch failed
                print(f"⚠️ Error in batch {batch_num}: {e}")
                print(f"⏳ Retrying batch {batch_num} in {retry_duration} seconds...")
                time.sleep(retry_duration)

    conn.close()
    print("✅ Cloud data tagging complete!")

if __name__ == "__main__":
    # Ensure this string points to your actual local SQLite database file
    tag_data("data/jobs.db")