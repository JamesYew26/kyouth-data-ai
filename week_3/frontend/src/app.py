import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Frontend Service")

# Resolve the absolute path to the templates directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serves the main chat page interface.
    """
    # Fix: Pass request as an explicit keyword argument
    return templates.TemplateResponse(
        request=request,
        name="chat_page.html",
        context={},  # Any other template variables go here
    )
