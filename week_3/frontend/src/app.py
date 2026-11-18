"""Frontend service: serves the single-page chat UI."""

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# The browser calls the backend directly, so this must be a URL reachable from the
# user's machine (e.g. http://localhost:8001/chat), not a Docker-internal hostname.
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001/chat")

app = FastAPI(title="Frontend Service")
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="chat_page.html", context={"backend_url": BACKEND_URL}
    )
