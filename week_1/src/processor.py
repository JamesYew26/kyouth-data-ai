import json
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator

# --- 1. THE DATA CONTRACT (Pydantic) ---

class JobListing(BaseModel):
    source_id: str
    job_title: str = Field(..., min_length=1)
    # Using Optional allows the script to pass validation even if the scraper misses a field
    company: Optional[str] = "Unknown Company"
    description: Optional[str] = "No description available"

    @field_validator('job_title', 'company', 'description', mode='before')
    @classmethod
    def clean_text(cls, v: str) -> str:
        """Removes extra whitespace and quopri artifacts."""
        if isinstance(v, str) and v.strip():
            return " ".join(v.split())
        return v

# --- 2. THE EXTRACTION LOGIC (BeautifulSoup) ---

def process_all_html(input_dir, output_dir):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    html_files = list(input_dir.glob("*.html"))
    stats = {"total": len(html_files), "success": 0, "failed": 0}

    print(f"🛠️ Starting Silver Stage: Processing {stats['total']} files...\n")

    for html_file in html_files:
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')

            og_url_tag = soup.find("meta", property="og:url")
            if not og_url_tag or not og_url_tag.get("content"):
                raise ValueError("Missing og:url for source_id extraction")
            
            url_path = og_url_tag["content"].rstrip('/')
            source_id = url_path.split('/')[-1]

            # --- IMPROVED SELECTORS ---
            # Jobstreet often uses data-automation attributes which are more stable than classes
            raw_data = {
                "source_id": html_file.stem,
                
                "job_title": (
                    soup.find('h1') or 
                    soup.find(attrs={"data-automation": "job-detail-title"})
                ).get_text(separator=" ", strip=True) if soup.find('h1') else None,

                "company": (
                    soup.find(attrs={"data-automation": "advertiser-name"}) or 
                    soup.find(class_='company') or
                    soup.find('span', class_='_19qz6600') # Common Jobstreet obfuscated class
                ).get_text(separator=" ", strip=True) if soup.find(class_='company') or soup.find(attrs={"data-automation": "advertiser-name"}) else None,

                "description": (
                    soup.find(attrs={"data-automation": "jobDescription"}) or 
                    soup.find(class_='description') or
                    soup.find('div', class_='_1798880') # Common Jobstreet obfuscated class
                ).get_text(separator=" ", strip=True) if soup.find(class_='description') or soup.find(attrs={"data-automation": "jobDescription"}) else None
            }

            

            # --- VALIDATION ---
            validated_job = JobListing(**raw_data)

            # --- SAVING ---
            json_path = output_dir / f"{html_file.stem}.json"
            json_path.write_text(validated_job.model_dump_json(indent=4))
            
            stats["success"] += 1
            print(f"✅ Processed: {html_file.name}")

        except ValueError as e:
            # This catches our manual "Missing" errors
            stats["failed"] += 1
            print(f"⚠️ {e} in: {html_file.name}")

    # --- FINAL REPORT ---
    print("\n")
    print(f"📊 Silver summary:")
    print(f"Total: {stats['total']} | Processed:  {stats['success']} | Skipped:    {stats['failed']} \n\n")

if __name__ == "__main__":
    # Ensure paths match your main.py constants
    process_all_html("data/1_bronze", "data/2_silver")