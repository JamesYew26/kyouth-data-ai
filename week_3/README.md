```markdown
# Full-Stack Containerized AI Chat & Resume Analysis Application

## Project Overview
The goal of this project is to build, configure, and containerize a full-stack, production-ready AI chat and resume skill-gap analysis application. The system features a decoupled microservices architecture comprising an interactive web frontend, a robust FastAPI backend service, and custom data-engineering modules that integrate with Large Language Models (LLMs) alongside local structured data stores. 

The application serves two distinct execution pathways:
1. **Conversational AI Mode**: An interactive chat interface routing natural language prompts to a Gemini generative LLM layer.
2. **Deterministic Skill-Gap Analyzer**: A specialized data pipeline that ingests a user's raw PDF or text resume, cross-references extracted technical profiles against an active SQLite job postings database, and maps out a clean array of missing technical competencies.

---

## Setup Instructions

### Prerequisites
Before setting up the environment, ensure your local host machine has the following tools installed:
* **Docker Engine** (v20.10.0 or higher)
* **Docker Compose** (v2.0.0 or higher)
* **Python 3.11+** with **`uv`** package manager *(Optional: Only required for standalone local execution outside of Docker)*

### Environment Configuration
The application requires specific runtime environment flags to manage network routing and secret API tokens securely.

1. Create a `.env` file at the root of your project repository:
```bash
   touch .env

```

2. Open the `.env` file and populate it with the following configuration variables (ensuring you swap in your live API key credentials):

```ini
   GEMINI_API_KEY=AIzaSyYourActualSecretKeyHere
   BACKEND_URL=http://localhost:8001/chat
   OLLAMA_HOST=[http://host.docker.internal:11434](http://host.docker.internal:11434)

```

> ⚠️ **Security Warning:** Never commit the `.env` file to version control. Ensure it is explicitly listed within your `.gitignore` rules.

### Running the Application with Docker Compose

The entire multi-container service stack is fully orchestrated via Docker Compose.

1. Execute the following single assembly command from your root repository directory to compile the service layers and boot the runtime cluster:

```bash
   docker compose up --build

```

2. Docker will pull the base images, construct the isolated frontend and backend layers, link volumes, and launch the network cluster.
3. To safely spin down the cluster and clean up container runtimes, execute:

```bash
   docker compose down -v

```

### Standalone Local Execution (Optional via `uv`)

If debugging or executing components natively without Docker containers:

1. Navigate to the backend service layout directory:

```bash
   cd backend

```

2. Install your lockfile package dependencies natively onto your machine using the modern `uv` workflow accelerator:

```bash
   uv pip install --system -r pyproject.toml

```

---

## Usage

### Accessing the Web Application

Once the Docker Compose logs show both services running successfully:

* Open your web browser and navigate to: **`http://localhost`** (or `http://127.0.0.1`)

### Executing User Input Workflows

The chat interface intelligently routes workflows based on the combination of inputs provided:

* **Scenario A: Text-Only Chat Messaging**
* *Input:* Type a natural language query (e.g., *"Explain how the internal bridge network works in Docker."*) and click **Send**.
* *Output:* The UI displays a conversational, streaming text response evaluated from the underlying Gemini model.


* **Scenario B: File-Only Resume Upload**
* *Input:* Select and attach a valid `.pdf` resume profile using the file picker component, leave the text input empty, and click **Send**.
* *Output:* The UI returns an exact, filtered array showing technical skill shortages mapped out relative to your internal database table entries: `gaps=['.net', 'aws', 'docker', 'fastapi']`.


* **Scenario C: Combined Text and File Payload**
* *Input:* Upload your resume file and concurrently write a tailored query instruction (e.g., *"Summarize my professional experience based on this file"*).
* *Output:* The system reads the document and passes the compiled text data structure along to the LLM to provide localized contextual insights.



---

## API / Function Reference

### Backend Endpoints: `POST /chat`

The FastAPI orchestration tier exposes a single primary routing gateway. Due to incoming data streams that merge raw text alongside file uploads, this interface leverages standard network Form Data constraints rather than raw application JSON payloads.

* **Request Type:** `multipart/form-data`
* **Payload Fields:**
* `message` *(Form String, Default: "")*: The user's typed chat text query instruction.
* `file` *(Binary File, Optional)*: The binary data stream representing the uploaded PDF or text file.


* **Response Format:**

```json
  {
    "reply": "gaps=['.net', 'aws', 'docker', 'fastapi']"
  }

```

### Key Frontend Core Architecture

The frontend utilizes optimized Vanilla HTML5/CSS3 structures driven by a modular JavaScript payload dispatcher.

* `handleSubmission()`: An asynchronous orchestrator that intercepts user interaction, verifies input states, constructs a runtime `FormData` instantiation container, appends current file/string targets, and executes network synchronization.
* `fetch('http://localhost:8001/chat')`: Initiates a network request boundary crossing over the local machine bridge to synchronize data with the containerized FastAPI cluster.
* `appendMessage(text, isUser)`: Dynamically handles the browser Document Object Model (DOM), safely wrapping backend payload returns into structural, scannable conversational layout components.

### Docker Network Architecture Cross-Communication

The application builds an isolated bridge network layer overlaying both microservices. The **frontend client runs directly inside the user's host browser context**, meaning its outbound requests query your machine's loopback interface (`http://localhost:8001/chat`).

Conversely, whenever internal services inside the containerized backend attempt to coordinate with third-party servers running on your machine (like an Ollama local model), they cross container network boundaries by communicating through the special host gateway alias endpoint: **`http://host.docker.internal`**.

---

## Data / Assumptions

### Data Routing Architecture

1. The user provides inputs via the browser DOM interface.
2. JavaScript transforms the state properties into a streaming `multipart/form-data` body packet and maps it to the network layer.
3. The FastAPI endpoint intercepts the packet, writing incoming file buffers to an isolated secure runtime memory directory (`/tmp/`).
4. The router evaluates the inputs: if a text-less file configuration is discovered, it shifts context control down into `find_skill_gaps.py`.
5. The pipeline queries the local SQLite data structure layer (`jobs_d1.db`), extracts matching dataset arrays, performs pure Python set subtraction arithmetic, and converts the results into a raw structured string response.

### System Assumptions & Constraints

* **Input Formats:** The backend expects clean, standard PDF or raw UTF-8 text file profiles. Uploading encrypted, corrupted, or password-protected files will invoke immediate pipeline block validation warnings.
* **Data Limits:** File uploads are processed via streaming memory chunks to guarantee low RAM footprints; however, files should remain under 25MB to minimize connection timeouts over basic network sockets.
* **Simplifications:** The internal `find_skill_gaps.py` matching module employs a strict case-insensitive string parsing logic block. It maps matching tokens deterministically rather than through semantic vectors.

---

## Testing

Each component across our decoupled application layers was tested individually to guarantee complete operational runtime parity and pinpoint bug vectors early.

### Frontend Test Suite

* **Input Field State Tests:** Verified that removing input criteria tags allows standalone file transmission without browser event listener execution lockouts.
* **UI Responsiveness Tests:** Verified that when text-less uploads occur, the UI renders the custom placeholder prompt message (*"Analyzing skill gaps..."*).

### Backend Network API Tests

To bypass browser constraints and ensure the FastAPI layer handles raw network packets flawlessly, you can replicate testing routines using `curl` directly within your host shell terminal:

* **Test Case 1: Testing Text-Only Routing Interaction**

```bash
  curl -X POST "http://localhost:8001/chat" \
    -F "message=Hello assistant"

```

* **Test Case 2: Testing Pure File Ingestion Submissions**

```bash
  curl -X POST "http://localhost:8001/chat" \
    -F "file=@/path/to/your/local/resume.pdf"

```

---

## Limitations

* **State and Session Tracking:** The system is entirely stateless. Chat session state variables and historical analysis profiles are not recorded to disk; refreshing the browser UI layout wipes the memory history clean.
* **Authentication Security:** The application includes zero user-access authorization boundaries, JWT middleware integrations, or rate-limiting protocols. It should only be deployed inside local development contexts.
* **LLM Accuracy Trade-offs:** Resume parsing precision relies entirely on the capability of the targeted Gemini foundation model. Complex multi-column design resume graphics formats or ambiguous keyword syntax definitions may alter extraction consistency.

---

## Architecture Reflection

### Design Choices

Choosing a microservices architecture that splits the frontend layout from the backend FastAPI engine guarantees high decoupling. Containerizing each module with separate Dockerfiles isolates our runtime system dependencies entirely.

The frontend needs zero complex node module footprints—running on a minimalist, highly lightweight Nginx or web-server container layer—while our Python backend completely packages complex analytics tools like `pypdf`, `sqlite3`, and `pydantic` in its own specialized system environment layer without polluting host computer resource footprints.

### Trade-offs

We chose to prioritize **deployment velocity and environment standardization via Docker Compose** over complex cloud-native architectures. This provides anyone launching the system an instant "one-click" runtime setup sequence.

Additionally, we prioritized **absolute accuracy and determinism for the skill-gap results** over an entirely AI-driven conversational assessment. By choosing pure Python set operations (`database_set - candidate_set`), we ensure the application output lists exactly what is missing from the job requirements database without text hallucinations.

### Future Improvements

Given more time and expanded development tracks, the application would scale up across three key axes:

1. **Robust UI Engineering Frameworks:** Porting the raw HTML/CSS framework layout into a responsive React or Vue component framework layer to achieve smooth modular tracking.
2. **Persistent Data Architecture:** Injecting a persistent database engine (such as PostgreSQL) to securely maintain historical user accounts, profile metrics, and chat history rows.
3. **Cloud Native Orchestration:** Moving the infrastructure boundaries beyond local machine configurations by targeting AWS ECS or Kubernetes clusters paired with fully managed cloud API gateways.

```

```