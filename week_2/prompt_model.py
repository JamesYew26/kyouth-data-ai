import sys
import os
from google import genai
from google.genai.errors import APIError, ClientError

def prompt_model(model: str, prompt: list) -> str:
    """Handles the raw API connection to Gemini."""
    client = genai.Client()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            'system_instruction': (
                "You are a strict data extraction tool. Analyze the provided job descriptions "
                "and output ONLY the requested format (source_id: tech1, tech2). Do not include "
                "any introductory text, explanations, or conversational filler."
            )
        }
    )
    return response.text

def main():
    print(f"Running prompt_model.py ...")
    prompt_model(sys.argv[1], sys.argv[2:])

if __name__ == "__main__":
    main()