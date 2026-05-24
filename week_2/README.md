## Project Overview

This project implements the AI-driven core of a **Skill Gap Detection Pipeline**. While rigid, rule-based systems struggle to handle highly varied and unpredictable text formats, this system leverages a Large Language Model (LLM) to intelligently identify semantic patterns and generate flexible interpretations of professional data.

Using unstructured job listings and user resumes as input, the pipeline automates two complex business logic tasks:

1. **Entity Extraction (`tag_data.py`):** Parses raw, unpredictable job descriptions from an SQLite database to extract precise technologies and tools, saving them directly into a structured technical stack column.
2. **Semantic Gap Analysis (`find_skill_gaps.py`):** Cross-references an applicant's resume against the dynamically extracted technical stack to surface missing core proficiencies, bypassing the limitations of simple, rigid keyword matching.

---

## Setup Instructions

### Prerequisites

* **Python Version:** Python 3.10 or higher
* **Package Manager:** `uv` (fast, modern Python package installer and resolver)
* **Database Engine:** SQLite3
* **External Access:** Valid LLM API credentials (e.g., OpenAI, Anthropic, or similar compatible provider)

### Local Environment Setup

1. **Clone & Navigate:** Prerequisite.
Open your terminal and navigate to your project directory:

```bash
cd skill-gap-detection-pipeline

```


2. **Initialize Virtual Environment:** Using uv.
Create a clean, isolated virtual environment using the `uv` toolchain:

```bash
uv venv

```

Activate it based on your operating system:

* **macOS/Linux:** `source .venv/bin/activate`
* **Windows (CMD):** `.venv\Scripts\activate.bat`
* **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`


3. **Install Dependencies:** Using uv sync/pip.
Install the required packages (such as your LLM SDK, dotenv, and database utilities) directly through `uv`:

```bash
uv pip install -r requirements.txt

```

*(Alternatively, if managing via an inline script declaration, `uv` will automatically provision dependencies upon execution).*


4. **Configure Environment Variables:** Security Check.
Create a `.env` file in the root directory of the project to securely house your API credentials. Do **not** commit this file to version control.

```env
# .env configuration template
LLM_API_KEY="your_actual_api_key_here"
DATABASE_PATH="jobs_d1.db"

```


---

## Usage

Ensure your source database (`jobs_d1.db` or `jobs.db`) is placed in the workspace root before running the scripts.

### 1. Tagging Skill Data from Job Descriptions

Run the extraction module to process raw job descriptions in the database and populate the `tech_stack` fields using the LLM.

```bash
uv run tag_data.py

```

* **Expected Input:** A database table rows containing unstructured text blocks like: *"Looking for an engineer experienced in building robust backend microservices with Laravel, processing data with Python, and working with SQL databases."*
* **Expected Output:** The database updates the target row's `tech_stack` column with structured data: `["Laravel", "Python", "SQL"]`.

### 2. Finding Skill Gaps Against a Resume

Run the analysis module to match a target candidate's resume text against your freshly updated database listings.

```bash
uv run find_skill_gaps.py

```

* **Expected Input:** A plain-text document (`resume_d3.txt`) outlining a candidate's background alongside the processed database rows.
* **Expected Output:** A terminal or file output highlighting precise gaps. For instance:
```text
=== SKILL GAP ANALYSIS REPORT ===
Target Position: Backend Data Engineer
Required Stack:  ['Laravel', 'Python', 'SQL']
Candidate Has:   ['Python', 'SQL', 'React', 'Java']
Identified Gaps: ['Laravel']

```



```

---

## API / Function Reference

### System Architecture Layout


```

```
              ┌──────────────────┐
              │      .env        │
              └─────────┬────────┘
                        │ (API Key)
                        ▼
              ┌──────────────────┐
              │   prompt_model   │
              └──────┬────┬──────┘
                     │    │
     ┌───────────────┘    └────────────────┐
     ▼                                     ▼

```

┌──────────────────┐                  ┌──────────────────┐
│    tag_data      │                  │  find_skill_gaps │
├──────────────────┤                  ├──────────────────┤
│ Extracts skills  │                  │ Evaluates gaps   │
│ from descriptions│                  │ against candidate│
│ into SQLite3     │                  │ resume_d3.txt    │
└──────────────────┘                  └────────────────└─┘

```

### Module: `prompt_model`
Houses the foundational configuration, model orchestrations, and client abstractions for communicating with the LLM API provider.

* **`generate_response(prompt: str, system_instruction: str = None) -> str`**
  * **Purpose:** Acts as the clean boundary interface to pass structured contextual blocks to the LLM and capture the raw string response.
  * **Inputs:** `prompt` (string containing data to analyze), `system_instruction` (optional behavioral constraints).
  * **Outputs:** A clean string output text containing generated evaluations or structured data blocks.

### Module: `tag_data`
Handles the primary database ingestion loop and entity extraction pipeline.

* **`extract_skills_from_description(description: str) -> list[str]`**
  * **Purpose:** Packages a single job description into an optimization prompt for execution by `prompt_model`.
  * **Inputs:** `description` (unstructured string text).
  * **Outputs:** A structured array/list of strings representing unique identified technologies.

### Module: `find_skill_gaps`
Evaluates professional alignments and targets missing skill sets.

* **`calculate_gaps(resume_text: str, target_tech_stack: list[str]) -> list[str]`**
  * **Purpose:** Generates a structured analysis mapping out which technical line items required by the company are unrepresented or missing within the candidate’s text footprint.
  * **Inputs:** `resume_text` (string), `target_tech_stack` (list of strings).
  * **Outputs:** A list of strings containing missing skills.

---

## Data / Assumptions

### Data Workflow


```

[jobs_d1.db / jobs.db] ──(Unstructured Job Text)──> [tag_data.py] ──(LLM)──> [tech_stack Column]
│
[resume_d3.txt] ───────────────────────────────────────────────────────────> [find_skill_gaps.py] ──> [Gap Report]

```

### Database & Input Footprint
* **Source Store:** SQLite3 database (`jobs_d1.db` or `jobs.db`).
* **Source Table Expectation:** Must contain a column capturing unstructured text descriptions (e.g., `job_description`), and a text/blob column designated for the output elements (`tech_stack`).
* **Resume Footprint:** A single unformatted flat text file named `resume_d3.txt`.

### Assumptions & Constraints
* **Format Flexibility:** The `tech_stack` target column stores extracted labels as structured string arrays (JSON array serialization string or comma-separated lists).
* **Language/Context Boundaries:** The LLM relies on contextual semantic understanding. Acronym variations or specialized industry nomenclature (e.g., *SQL Server* vs *MSSQL*) are handled seamlessly by the model's pattern recognition rather than absolute keyword strings.

---

## Testing

### Test Strategies & Scenarios
1. **Deterministic Input Validations:** Verifying that a known mock job description containing explicitly listed frameworks (e.g., *"Must know React and Python"*) results in a standardized output array `["React", "Python"]`.
2. **Edge-Case Parsing Tests:** Passing highly ambiguous descriptions (e.g., stories about working in a team environment with no mentioned stack) to confirm the extraction gracefully handles and outputs empty tracking definitions `[]` without error.
3. **Resume Boundary Assertions:** Mocking explicit resume text profiles to verify that gap calculation logic strictly catches missing parameters rather than surfacing matching items.

### Reproducing Tests
Locally execute validation suites using standard testing fixtures:
```bash
uv run -m pytest tests/

```

---

## Limitations

* **Context Window Boundaries:** Massive text documents or exceptionally long historical database files can hit context limits or incur elevated token processing costs.
* **Deterministic Behavior Trade-Off:** Moving from strict code logic rules to generative model intelligence introduces small variances in response styles. Exact casing or ordering of output strings can fluctuate across API updates.
* **Database Interactivity Limitations:** The logic handles offline batch execution over pre-existing static records and does not native-stream live operational modifications in real time without active polling wrappers.

---

## Architecture Reflection

### Design Choices

* **Centralized LLM Handling:** Consolidating execution through `prompt_model` isolates our reliance on the LLM API provider. If the core API signature changes or we swap models, we only modify a single file without rewriting downstream business logic.
* **Decoupled Job Tagging and Gap Analysis:** Separating data extraction (`tag_data`) from evaluation (`find_skill_gaps`) guarantees modularity. The tagged skills remain persistent in our database layer, eliminating the need to re-run expensive LLM extractions every time a new candidate runs an evaluation.

### Trade-offs

* **Scalability vs. Cost-Efficiency:** We chose rich semantic understanding over cheap computational execution. While a regex pattern matches text in milliseconds for free, it misses implicit mentions or unconventional formatting. Using an LLM increases processing time and introduces token costs, but provides significantly higher accuracy and adaptability for varied inputs.

### Future Improvements

* **Structured JSON Outputs:** Migrate raw prompt extractions to strict structured schemas using Pydantic validation boundaries to entirely eliminate parsing exceptions.
* **Vector Embeddings Cache:** Introduce vector embedding representations of skills to resolve synonym mapping natively (e.g., recognizing that a candidate with "Express.js" fits a "Node.js Developer" job stack requirement without manual rules).