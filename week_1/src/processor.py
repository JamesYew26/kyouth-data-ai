import json
from pathlib import Path
from typing import Optional
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator

# --- 1. THE DATA CONTRACT (Pydantic) ---

class JobListing(BaseModel):
    source_id: str
    job_title: str = Field(..., min_length=1)
    company: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)

    @field_validator('job_title', 'company', 'description', mode='before')
    @classmethod
    def clean_text(cls, v: str) -> str:
        """Removes extra whitespace."""
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

    for html_file in html_files:
        try:
            content = html_file.read_text(encoding='utf-8', errors='ignore')
            soup = BeautifulSoup(content, 'html.parser')

            # --- 1. EXTRACT SOURCE_ID ---
            og_url_tag = soup.find("meta", property="og:url")
            if not og_url_tag or not og_url_tag.get("content"):
                raise ValueError("Missing og:url meta tag")
            source_id = og_url_tag["content"].rstrip('/').split('/')[-1]

            # --- 2. EXTRACT DESCRIPTION ---
            desc_el = (
                # soup.find("meta", property="og:description") or
                soup.find("div", attrs={"data-automation": "jobAdDetails"}) or 
                soup.find(class_='description')
            )
            
            description = None
            if desc_el:
                # Use .get("content", "") to avoid None.strip() crashes
                if desc_el.name == 'meta':
                    description = desc_el.get("content", "").strip()
                else:
                    description = desc_el.get_text(separator=" ", strip=True)

            # --- 3. EXTRACT TITLE & COMPANY ---
            job_title_el = soup.find('h1') or soup.find(attrs={"data-automation": "job-detail-title"})
            company_el = (
                soup.find(attrs={"data-automation": "advertiser-name"}) or 
                soup.find(class_='company')
            )

            # --- 4. THE ERROR GUARDS ---
            if not job_title_el:
                raise ValueError("Missing job_title")
            if not company_el:
                raise ValueError("Missing company")
            if not description or len(description) < 1:
                raise ValueError("Missing description")

            # --- 5. BUILD RAW DATA ---
            raw_data = {
                "source_id": source_id,
                "job_title": job_title_el.get_text(separator=" ", strip=True),
                "company": company_el.get_text(separator=" ", strip=True),
                "description": description
            }

            # --- 6. VALIDATION & SAVING ---
            validated_job = JobListing(**raw_data)
            
            json_path = output_dir / f"{html_file.stem}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(validated_job.model_dump_json(indent=4))
            
            # MOVE THIS INSIDE THE TRY BLOCK
            stats["success"] += 1
            print(f"✅ Processed: {html_file.name}")

        except ValueError as e:
            stats["failed"] += 1
            print(f"⚠️ {e} in: {html_file.name}")
        
        except Exception as e:
            # Catch Pydantic ValidationErrors or other unexpected crashes
            stats["failed"] += 1
            print(f"❌ Unexpected Error in {html_file.name}: {e}")

    # --- FINAL REPORT ---
    print(f"\n📊 Silver summary: Total: {stats['total']} | Processed: {stats['success']} | Skipped: {stats['failed']}\n")

if __name__ == "__main__":
    process_all_html("data/1_bronze", "data/2_silver")