import sqlite3
from typing import List
from pydantic import BaseModel


class SkillGapResult(BaseModel):
    gaps: List[str]


def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
    # 1. Read and clean the resume file safely
    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except Exception as e:
        print(f"❌ Error reading resume: {e}")
        return SkillGapResult(gaps=[])

    # Clean text: replace punctuation with spaces to isolate tokens like 'c' and 'c++'
    cleaned_text = raw_text.replace(",", " ").replace("/", " ").lower()
    resume_words = set(cleaned_text.split())

    # 2. Connect to the database and fetch required skills
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()

        cursor.execute("SELECT tech_stack FROM jobs")
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return SkillGapResult(gaps=[])

    # 3. Process database skills into a lowercase set
    required_skills = set()
    for row in rows:
        if row[0]:
            # Assuming skills in the database might be comma-separated strings
            # We clean them the same way as the resume
            db_skill = row[0].lower().strip()
            required_skills.add(db_skill)

    # 4. Find the missing skills deterministically using set difference
    # This finds everything in required_skills that is NOT in resume_words
    gap_set = required_skills.difference(resume_words)

    # 5. Sort the results alphabetically as required
    sorted_gaps = sorted(list(gap_set))

    # Return the final Pydantic model
    return SkillGapResult(gaps=sorted_gaps)


if __name__ == "__main__":
    # 1. Capture the result from the function execution
    result = find_skill_gaps("data/resume_d3.txt", "data/jobs.db")

    # 2. Print the result so you can read it in the terminal
    print(result)
