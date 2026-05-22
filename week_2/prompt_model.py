import sys
import os
from google import genai
from openai import OpenAI
from google.genai.errors import APIError, ClientError

def prompt_model(model: str, prompt: list, system_instruction: str) -> str:
    """
    Dynamically routes your prompt to Gemini or Ollama, using
    the specific system instructions passed in by the caller.
    """
    # 🌐 ROUTE 1: Google Gemini Cloud API
    if 'gemini' in model.lower():
        print(f"📡 Routing to Google Cloud API ({model})...")
        client = genai.Client()
        
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config={'system_instruction': system_instruction}  # Passed dynamically!
        )
        return response.text

    # 💻 ROUTE 2: Local Ollama Models
    else:
        print(f"🏠 Routing to Local Ollama Server ({model})...")
        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama"
        )
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instruction},  # Passed dynamically!
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content

def main():
    print(f"Running prompt_model.py ...")
    prompt_model(sys.argv[1], sys.argv[2:])

if __name__ == "__main__":
    main()