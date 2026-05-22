# tag_data.py
import sqlite3
import time
from prompt_model import prompt_model  # 🔌 Connecting our two files

def tag_data(db_url: str):
    """
    Reads job descriptions from a SQLite database, uses Gemini or a local model via 
    prompt_model.py to extract the technical stack, and updates the database 
    safely in batches.
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

    # Configuration for batching and rate limiting
    batch_size = 5
    retry_duration = 70  # Safe cooldown window to clear rate limits if they hit
    pacing_duration = 10 # Mandatory pause between successful batches for cloud models
    model_name = 'gemma3'  # Current model choice

    print(f"📋 Found {len(rows)} rows to process. Starting batch updates...")
    
    # 3. Loop through the data in batches
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        batch_num = i // batch_size  # Starts at 0 to match your [Batch 0] format
        
        success = False
        attempt = 1  # 🔢 Track the current attempt for this batch
        
        while not success:
            try:
                # Construct the prompt for this specific batch
                prompt = (
                    f"Analyze the following job description and extract all specific technologies, "
                    f"programming languages, frameworks, databases, and tools mentioned (e.g., Git, AWS, CI/CD).\n\n"
                )

                extraction_instruction = (
                    "You are a precise data extraction tool. Output ONLY a flat, comma-separated list "
                    "of the extracted technologies. Do not include introductory text, bullet points, "
                    "markdown formatting, source IDs, or explanations. "
                    "Example output: Git, GitHub Actions, AWS, GCP, Azure"
                )
                
                for source_id, description in batch:
                    prompt += f"Source ID {source_id}:\n{description}\n\n"
                
                # Call the external module function
                print(f"🧠 Sending batch {batch_num} to {model_name}...")
                llm_response = prompt_model(model_name, prompt, extraction_instruction)
                print(f"📥 Response received for batch {batch_num}.")
                
                # Parse the model's response line by line
                parsed_updates = []
                lines = llm_response.split('\n')
                
                for line in lines:
                    if ":" in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            # Keep source_id as a string or integer matching your database schema
                            source_id = parts[0].strip()
                            tech_stack = parts[1].strip()
                            parsed_updates.append((tech_stack, source_id))
                
                # 4. Save changes as long as at least one row was successfully parsed
                if parsed_updates:
                    update_query = "UPDATE jobs SET tech_stack = ? WHERE source_id = ?;"
                    cursor.executemany(update_query, parsed_updates)
                    conn.commit()
                    
                    # 🎉 Print each successfully analyzed job in your exact format
                    for tech_stack, source_id in parsed_updates:
                        print(f"Analyzed Job {source_id}: {tech_stack}\n")
                        print(f"="*20)
                else:
                    # If absolutely zero lines could be parsed, it's a complete format failure
                    raise ValueError("No valid formatted lines could be parsed from the response.")
                
                success = True  # Move to the next batch since we saved what we could!
                
                # Pacing delay specifically for cloud models
                if 'gemini' in model_name.lower():
                    print(f"💤 Pacing... pausing for {pacing_duration} seconds before starting the next batch.\n")
                    time.sleep(pacing_duration)
                
            except Exception as e:
                # ⚠️ Print the exact failure format you requested
                print(f"[Batch {batch_num}] Attempt {attempt} failed: {e}")
                attempt += 1  
                print(f"⏳ Waiting {retry_duration} seconds before retrying...")
                time.sleep(retry_duration)

    conn.close()
    print("✅ Cloud data tagging complete!")

if __name__ == "__main__":
    tag_data("data/jobs_d1.db")