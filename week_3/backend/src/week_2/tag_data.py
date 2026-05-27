import json
import sqlite3
import time
from prompt_model import prompt_model


def tag_data(db_url: str):
    # Pipeline Constants
    BATCH_SIZE = 1
    MAX_RETRIES = 3
    MODEL_NAME = "deepseek"

    try:
        conn = sqlite3.connect(
            db_url, timeout=30.0
        )  # High timeout to prevent quick locks
        cursor = conn.cursor()
    except Exception as e:  # noqa: BLE001
        print(f"CRITICAL: Failed to connect to database at {db_url}: {e}")
        return

    try:
        # 1. Fetch all pending source_ids and descriptions to process
        cursor.execute(
            """
            SELECT source_id, description 
            FROM jobs
            WHERE tech_stack IS NULL OR tech_stack = ''
        """
        )
        all_jobs = cursor.fetchall()

        if not all_jobs:
            print("No pending jobs to process.")
            return

        # 2. Segment jobs into explicit batches
        batches = [
            all_jobs[i : i + BATCH_SIZE] for i in range(0, len(all_jobs), BATCH_SIZE)
        ]

        for batch_idx, batch in enumerate(batches, start=1):
            # Construct a clean payload representing the batch
            batch_data = [
                {"source_id": str(row[0]), "description": row[1]} for row in batch
            ]

            success = False
            attempt = 0
            wait_time = 2.0  # Initial retry backoff delay in seconds

            while attempt < MAX_RETRIES and not success:
                attempt += 1
                try:
                    # Construct strict prompt ensuring structured output mapping back to unique IDs
                    prompt = f"""
You are a technical data extractor. Analyze the following list of job applications provided in a JSON format.
For each job, extract the technical stack (programming languages, frameworks, databases, APIs, enterprise systems, and tools mentioned) as a single comma-separated string.

Return your response ONLY as a valid JSON object where the keys are the exact string 'source_id's provided, and the values are the comma-separated tech stack strings. Do not wrap the JSON in markdown blocks (like ```json).

Input Data:
{json.dumps(batch_data)}
                    """.strip()

                    # Call LLM interface
                    response_raw = prompt_model(MODEL_NAME, prompt)

                    # Clean up response if LLM accidentally used markdown code blocks
                    if response_raw.startswith("```"):
                        response_raw = (
                            response_raw.strip("`").replace("json\n", "", 1).strip()
                        )

                    # Parse response safely
                    parsed_response = json.loads(response_raw)

                    # Prepare batch update collection
                    updates = []
                    for row in batch:
                        s_id = str(row[0])
                        if s_id in parsed_response:
                            tech_string = str(parsed_response[s_id]).strip()
                            updates.append((tech_string, row[0]))

                    # 3. Resilient Database Write for the Batch
                    if updates:
                        cursor.executemany(
                            """
                            UPDATE jobs 
                            SET tech_stack = ? 
                            WHERE source_id = ?
                        """,
                            updates,
                        )
                        conn.commit()

                        # Print explicit individual row success logs
                        for tech_string, orig_id in updates:
                            print(f"Analyzed Job [{orig_id}]: {tech_string}")

                    success = True  # Batch completed safely

                except (json.JSONDecodeError, TypeError, KeyError) as parse_err:
                    print(
                        f"[Batch {batch_idx}] Attempt {attempt} failed: "
                        f"Malformed LLM payload or parsing mismatch. Details: {parse_err}"
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(wait_time)
                        wait_time *= 2.0

                except sqlite3.OperationalError as db_err:
                    print(
                        f"[Batch {batch_idx}] Attempt {attempt} failed: Database lock or operational exception. {db_err}"
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(wait_time)
                        wait_time *= 2.0

                except Exception as general_err:  # noqa: BLE001
                    print(
                        f"[Batch {batch_idx}] Attempt {attempt} failed: Unexpected runtime or LLM disconnect exception. {general_err}"
                    )
                    if attempt < MAX_RETRIES:
                        time.sleep(wait_time)
                        wait_time *= 2.0

            if not success:
                print(
                    f"[Batch {batch_idx}] Completely failed after {MAX_RETRIES} attempts. Skipping to next batch."
                )

    except Exception as fatal_pipeline_err:  # noqa: BLE001
        print(
            f"An unhandled structural anomaly occurred inside the pipeline wrapper: {fatal_pipeline_err}"
        )
    finally:
        try:
            conn.close()
        except sqlite3.Error:
            pass


if __name__ == "__main__":
    tag_data("data/jobs_d1.db")
