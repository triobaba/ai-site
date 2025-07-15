from __future__ import annotations

import os
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dotenv import load_dotenv, find_dotenv

# Load environment variables from the nearest .env file up the directory tree.
load_dotenv(find_dotenv(), override=False)

try:
    from openai import OpenAI
except ImportError as e:  # pragma: no cover
    raise RuntimeError("The 'openai' package is required. Install via 'pip install -r requirements.txt'.") from e

# ---------------------------------------------------------------------------
# Configuration & OpenAI client
# ---------------------------------------------------------------------------
OPENAI_API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("openai_api_key")  # allow lowercase in .env
    or os.getenv("OPENAI_KEY")       # optional alias
)
if not OPENAI_API_KEY:
    raise RuntimeError("Environment variable OPENAI_API_KEY is not set.")

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# FastAPI app setup
# ---------------------------------------------------------------------------
app = FastAPI(title="AI Site Search", version="0.1.0", docs_url="/docs")

# Allow local dev frontend (Vite) and other origins during test; tighten in prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React build (if present)
build_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
# Mount built React assets under /static to avoid overriding /api routes.
if os.path.isdir(build_dir):
    app.mount("/static", StaticFiles(directory=build_dir), name="static")

# ---------------------------------------------------------------------------
# Pydantic model for the API request/response
# ---------------------------------------------------------------------------
class SearchRequest(BaseModel):
    site: str
    question: str

class Citation(BaseModel):
    index: int
    url: str

class SearchResponse(BaseModel):
    answer: str
    citations: List[Citation] | None = None

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _normalize_site(site: str) -> str:
    site = site.strip()
    if site.startswith("https://"):
        site = site.removeprefix("https://")
    elif site.startswith("http://"):
        site = site.removeprefix("http://")
    return site

# ---------------------------------------------------------------------------
# API endpoint
# ---------------------------------------------------------------------------
@app.post("/api/search", response_model=SearchResponse)
async def api_search(req: SearchRequest):
    site = _normalize_site(req.site)
    if not site:
        raise HTTPException(status_code=400, detail="Invalid site URL")

    if not req.site.startswith("http"):
        site_filter = f"https://www.{site}"  # ensure scheme
    else:
        site_filter = req.site.rstrip("/")

    # build search_prompt
    variants = [f"site:{site}"]
    if not site.startswith("www."):
        variants.append(f"site:www.{site}")
    search_prompt = f"{' OR '.join(variants)} {req.question.strip()}"

    system_prompt = (
        f"You are a helpful assistant. You must base your answer only on pages "
        f"from the domain '{site}'. If you cannot find relevant information "
        f"there, reply exactly: 'No information found on {site}.'"
    )
    try:
        response = client.responses.create(
            model="gpt-4o",  # web-search capable model
            tools=[{"type": "web_search"}],
            input=search_prompt,
            instructions=system_prompt,
        )
    except Exception as exc:
        # ensure ASCII-safe
        msg = str(exc)
        try:
            msg.encode("ascii")
        except UnicodeEncodeError:
            msg = msg.encode("ascii", "backslashreplace").decode()
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"error": msg})

    answer: str = response.output_text  # type: ignore[attr-defined]
    citations_raw: List[Dict[str, Any]] = getattr(response, "citations", [])  # type: ignore[attr-defined]
    citations = [Citation(index=c["index"], url=c["url"]) for c in citations_raw] if citations_raw else None
    return SearchResponse(answer=answer, citations=citations)

# ---------------------------------------------------------------------------
# Fallback route for client-side routing in React (only if build exists)
# ---------------------------------------------------------------------------
if os.path.isdir(build_dir):
    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):  # pylint: disable=unused-argument
        """Serve React index.html for non-API GET routes."""
        # If the request is for /api/... we let FastAPI handle 404/405 as usual
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        index_file = os.path.join(build_dir, "index.html")
        return FileResponse(index_file) 