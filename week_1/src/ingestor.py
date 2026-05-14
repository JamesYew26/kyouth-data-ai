import sys
import email
from pathlib import Path

# Move these inside the function or keep as constants, but don't run logic here
def decode_single_file(mhtml_file, output_path):
    """Helper to decode a single MHTML file to HTML."""
    try:
        with open(mhtml_file, 'rb') as f:
            msg = email.message_from_binary_file(f)
            for part in msg.walk():
                if part.get_content_type() == 'text/html':
                    html_data = part.get_payload(decode=True)
                    output_path.write_bytes(html_data)
                    return True
        return False
    except Exception:
        return False

def ingest_all_mhtml(input_dir, output_dir):
    """The function called by main.py."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_files = list(input_dir.glob("*.mhtml"))
    total_files = len(all_files)
    success_count = 0
    failed_count = 0

    

    for file in all_files:
        new_filename = file.stem + ".html"
        target_path = output_dir / new_filename
        
        if decode_single_file(file, target_path):
            success_count += 1
            print(f"✅ Extracted: {new_filename}")
        else:
            failed_count += 1
            print(f"⚠️ Failed: {file.name}")

    print(f"\n📊 Bronze Summary: Total: {total_files} | Extracted: {success_count} | Failed: {failed_count}\n")

# --- THIS PREVENTS AUTO-RUNNING ---
if __name__ == "__main__":
    # This only runs if you run 'python3 ingestor.py' directly
    source = Path("data/0_source")
    bronze = Path("data/1_bronze")
    ingest_all_mhtml(source, bronze)