# /// script
# dependencies = [
#     "google-genai",
#     "ollama",
#     "python-dotenv",
# ]
# ///

import os
import sys
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
import ollama

# Load environment variables from a .env file if present
load_dotenv()

def query_gemini(model_name: str, prompt: str) -> str:
    """Queries the Google Gemini API using the modern google-genai SDK."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("\n❌ Error: GEMINI_API_KEY is missing from your environment.", file=sys.stderr)
        print("Please create a '.env' file in this directory and add:", file=sys.stderr)
        print("  GEMINI_API_KEY=your_actual_api_key_here\n", file=sys.stderr)
        sys.exit(1)

    # Map generic alias to the current recommended default if needed
    if model_name == "gemini":
        model_name = "gemini-2.5-flash-lite"

    try:
        # Client automatically picks up GEMINI_API_KEY from the environment
        client = genai.Client()
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        return response.text
    except APIError as e:
        print(f"\n❌ Google Gemini API Error: {e.message}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred while contacting Gemini: {e}", file=sys.stderr)
        sys.exit(1)

def query_ollama(model_name: str, prompt: str) -> str:
    """Queries a local model via the Ollama client library."""

    if model_name=="deepseek":
        model_name="deepseek-r1:1.5b"
    try:
        response = ollama.generate(model=model_name, prompt=prompt)
        return response['response']
    except ollama.ResponseError as e:
        if e.status_code == 404:
            print(f"\n❌ Ollama Error: The model '{model_name}' is not downloaded.", file=sys.stderr)
            print(f"Please run `ollama pull {model_name}` in your terminal first.", file=sys.stderr)
        else:
            print(f"\n❌ Ollama API Error: {e.error}", file=sys.stderr)
        sys.exit(1)
    except Exception:
        print("\n❌ Error: Could not connect to Ollama.", file=sys.stderr)
        print("Make sure the Ollama application is running locally on your machine.", file=sys.stderr)
        sys.exit(1)

def prompt_model(model: str, prompt: str) -> str:
    """Routes the incoming prompt to either Gemini or a local Ollama instance

    based on the specified model string name.
    """
    if model.lower().startswith("gemini"):
        return query_gemini(model, prompt)
    else:
        return query_ollama(model, prompt)

def main():
    parser = argparse.ArgumentParser(
        description="Prompt cloud (Gemini) or local (Ollama) LLMs from the command line.",
        usage='uv run prompt_model.py <model_choice> "<your_prompt>"'
    )
    parser.add_argument(
        "model", 
        help="Use 'gemini' or 'gemini-2.5-flash' for Google, or any installed Ollama model (e.g., 'phi3', 'llama3')."
    )
    parser.add_argument(
        "prompt", 
        help="The prompt string to send to the model."
    )

    # Handle missing arguments cleanly before argparse raises a generic error
    if len(sys.argv) < 3:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    print(f"🤖 Sending prompt to '{args.model}'...")
    
    # Execute through the requested wrapper function
    result = prompt_model(args.model, args.prompt)

    print("\n--- Response ---")
    print(result)
    print("----------------")

if __name__ == "__main__":
    main()