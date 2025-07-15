# Site Search Webapp

## Prerequisites

- Python 3.10+
- Node 18+
- `OPENAI_API_KEY` with access to `gpt-4o` web-search preview

## Setup

```bash
# backend deps
pip install -r requirements.txt

# frontend deps
cd frontend
npm install  # or yarn / pnpm
```

## Running locally (development)

```bash
# 1. start Vite dev server (frontend)
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173

# 2. in another terminal start FastAPI backend
export OPENAI_API_KEY=sk-...
cd ..  # back to webapp
uvicorn fastapi_app:app --reload --port 8000
```

Access: http://localhost:5173 (frontend proxies API calls to the same origin during prod build; in dev you may tweak the fetch URL or use a proxy).

## Building for production

```bash
cd frontend
npm run build
```

After `npm run build`, the artifacts land in `frontend/dist`. FastAPI automatically serves that directory (see `fastapi_app.py`). Start the server:

```bash
export OPENAI_API_KEY=sk-...
uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT
```

Deploy on Render/Docker with:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY webapp/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY webapp/fastapi_app.py ./

# copy pre-built frontend (built in CI beforehand)
COPY webapp/frontend/dist ./frontend/dist
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "$PORT"]
``` 