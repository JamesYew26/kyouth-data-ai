import json
import logging
import sqlite3
import time
from typing import List, Set
from pydantic import BaseModel

# Mocking or assuming the existence of the requested module
# from prompt_model import prompt_model

# Configure logging to standard output as required
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class SkillGapResult(BaseModel):
    gaps: List[str]


def clean_skill(skill: str) -> str:
    """
    Normalizes a skill string to ensure exact matching and reduce variations.
    Converts to lowercase, strips whitespace, and standardizes common edge cases.
    """
    s = skill.lower().strip()
    # Normalize common dotnet variations deterministically
    if s in ("dotnet", ".net core", "dot net"):
        return ".net"
    return s


def call_llm_with_retry(file_path: str, max_retries: int = 3, base_delay: float = 2.0) -> List[str]:
    """
    Reads the resume file and invokes the LLM to extract skills with exponential backoff.
    """
    # Import inside the function or assume top-level import per constraints
    from prompt_model import prompt_model

    with open(file_path, "r", encoding="utf-8") as f:
        resume_text = f.read()

    prompt = (
        "Extract all technical skills, programming languages, frameworks, tools, and databases "
        "mentioned in the following resume. Return ONLY a valid JSON array of lowercase strings. "
        "Preserve compound terms exactly as written (e.g., 'c/c++', '.net', 'react native'). "
        "Do not include any markdown formatting, wrappers, conversational text, or explanations.\n\n"
        f"Resume Text:\n{resume_text}"
    )

    delay = base_delay
    for attempt in range(max_retries + 1):
        try:
            # Using 'gemini-1.5-flash' as a highly reliable fast processing model
            raw_response = prompt_model("gemini-3-flash-preview", prompt)

            
            # Clean up potential markdown code block wrappers if the LLM slips up
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()


            skills = json.loads(cleaned_response)
            if isinstance(skills, list):
                return [clean_skill(str(skill)) for skill in skills]
            
            raise ValueError("LLM did not return a JSON array structure.")
            
        except Exception as e:
            if attempt == max_retries:
                logging.error(f"LLM invocation failed after {max_retries} retries: {e}")
                raise e
            logging.warning(f"LLM attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

    return []


def fetch_db_skills_batched(db_url: str, batch_size: int = 500, max_retries: int = 3, base_delay: float = 2.0) -> Set[str]:
    """
    Queries the SQLite jobs table in chunks to prevent memory bloat, using exponential backoff.
    """
    db_skills = set()
    delay = base_delay
    
    for attempt in range(max_retries + 1):
        conn = None
        try:
            conn = sqlite3.connect(db_url)
            cursor = conn.cursor()
            
            
            cursor.execute("SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL")
            
            while True:
                rows = cursor.fetchmany(batch_size)
                print("db success")
                if not rows:
                    break
                
                for (tech_stack_str,) in rows:
                    # Split comma-separated database tokens
                    for raw_skill in tech_stack_str.split(","):
                        cleaned = clean_skill(raw_skill)
                        if cleaned:
                            db_skills.add(cleaned)
            
            return db_skills

        except sqlite3.Error as e:
            if attempt == max_retries:
                logging.error(f"Database read failed after {max_retries} retries: {e}")
                raise e
            logging.warning(f"Database attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2
        finally:
            if conn:
                conn.close()
                
    return db_skills


def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
    """
    Identifies missing technical skills deterministically by comparing a candidate's 
    resume text against a jobs database tech_stack.
    """
    # Deterministic exclusion set to strip out soft skills or non-technical terms
    NON_TECHNICAL_EXCLUSIONS = {
        "leadership", "management", "project management", "communication", 
        "agile", "scrum", "teamwork", "problem solving", "interpersonal skills",
        "pmp", "scrum master"
    }

    try:
        # Step 1: Semantic Extraction (LLM Phase)
        candidate_skills_list = call_llm_with_retry(input_file_path)
        candidate_skills_set = set(candidate_skills_list)


        # Step 2: Read Target Skills (Deterministic Database Batch Phase)
        database_skills_set = fetch_db_skills_batched(db_url)


        # Step 3: Filter, Compute Gaps, and Normalize (Pure Python Processing)
        # Apply the hardcoded exclusion filters to both sets
        filtered_candidate_skills = candidate_skills_set - NON_TECHNICAL_EXCLUSIONS
        filtered_database_skills = database_skills_set - NON_TECHNICAL_EXCLUSIONS


        # Calculate semantic gap via set difference
        gap_set = filtered_database_skills - filtered_candidate_skills

        # Enforce 100% determinism via alphabetical sorting
        sorted_gaps = sorted(list(gap_set))
        print(f"gaps={sorted_gaps}")
        return SkillGapResult(gaps=sorted_gaps)
    
    

    except Exception as final_error:
        # Step 4: Robust Error Handling (Never throw an unhandled exception or crash)
        logging.error(f"Critical error encountered in find_skill_gaps pipeline: {final_error}")
        return SkillGapResult(gaps=[])
    
if __name__ == "__main__":
    find_skill_gaps("data/resume_d3.txt", "data/jobs_d1.db")