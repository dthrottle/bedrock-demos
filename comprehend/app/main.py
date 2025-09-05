from __future__ import annotations

import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .comprehend_service import ComprehendService, curate_for_ui

# Load environment variables from a .env file if present (searched upward)
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")

try:
    CHAR_LIMIT = int(os.getenv("CHAR_LIMIT", "2000"))
except ValueError:
    CHAR_LIMIT = 2000

app = FastAPI(title="Amazon Comprehend Demo", version="0.1.0")

static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)

service = ComprehendService(region=os.getenv("AWS_REGION"))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):  # noqa: D401 minimal doc per spec simplicity
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "result": None, "text": "", "limit": CHAR_LIMIT, "error": None},
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, text: str = Form(...)):
    text_input = text.strip()
    error = None
    result_payload = None
    if not text_input:
        error = "Please enter some text."
    elif len(text_input) > CHAR_LIMIT:
        error = f"Input exceeds {CHAR_LIMIT} character limit ({len(text_input)})."
    else:
        logger.info("Analyzing text length=%s", len(text_input))
        comp = service.analyze(text_input)
        result_payload = curate_for_ui(comp)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "result": result_payload,
            "text": text_input,
            "limit": CHAR_LIMIT,
            "error": error,
        },
    )


@app.get("/health")
async def health():  # noqa: D401
    return {"status": "ok"}


def run():  # convenience for `python -m app.main`
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    try:
        port = int(os.getenv("APP_PORT", "8000"))
    except ValueError:
        port = 8000
    uvicorn.run("app.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    run()
