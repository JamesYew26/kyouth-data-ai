import os
import shutil
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pypdf import PdfReader  # ✅ Back for backend extraction tracking

# Import your core modules
from week_2.prompt_model import prompt_model
from week_2.find_skill_gaps import find_skill_gaps

# Explicitly load environment variables from the root backend/.env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


app = FastAPI(title="LLM Chat Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = "data/jobs_d1.db"


@app.post("/chat", status_code=status.HTTP_200_OK)
async def chat_endpoint(
    message: str = Form(""), file: Optional[UploadFile] = File(None)
):
    temp_file_path = None  # ✅ Standardized variable name
    user_query = message.strip()

    try:
        # --- SCENARIO 1: ONLY PDF IS UPLOADED (No text message) ---
        if file and not user_query:
            print(
                f"--- [FLOW 1] Routing raw file path directly to find_skill_gaps pipeline ---"
            )

            # Save raw file container to temp disk path so pipeline can open it
            temp_file_path = f"/tmp/{file.filename}"
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Execute pipeline and receive the exact SkillGapResult instance object class
            gap_analysis_result = find_skill_gaps(
                input_file_path=temp_file_path, db_url=DATABASE_URL
            )

            # Extract the raw sorted string array from the class schema variable
            raw_gaps_list = gap_analysis_result.gaps

            # Return it in the response matching your desired layout format string
            return {"reply": f"gaps={raw_gaps_list}"}

        # --- SCENARIO 2: USER SENDS BOTH MESSAGE AND PDF ---
        elif file and user_query:
            print(
                f"--- [FLOW 2] Injected Conversational Prompt Model with File Context ---"
            )

            pdf_reader = PdfReader(file.file)
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"

            combined_prompt = (
                f"Context from uploaded Resume:\n"
                f"--- START EXTRACT ---\n{extracted_text}\n--- END EXTRACT ---\n\n"
                f"User Instruction: {user_query}"
            )

            llm_output = prompt_model("gemini", combined_prompt)
            return {"reply": llm_output}

        # --- SCENARIO 3: USER ONLY SENDS A MESSAGE (No file) ---
        elif user_query and not file:
            print(
                f"--- [FLOW 3] Standard Conversational Chat routed directly to prompt_model ---"
            )

            llm_output = prompt_model("gemini", user_query)
            return {"reply": llm_output}

        else:
            return {
                "reply": "Please send a message query or upload a file profile to start."
            }

    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while routing the payload: {str(e)}",
        )
    finally:
        # Clean up temporary disk file footprints safely
        if temp_file_path and os.path.exists(
            temp_file_path
        ):  # ✅ Standardized variable name
            os.remove(temp_file_path)
