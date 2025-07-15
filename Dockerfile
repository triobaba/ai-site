FROM node:18 AS frontend-builder
WORKDIR /app
COPY frontend ./frontend
RUN cd frontend \
    && npm install --legacy-peer-deps --no-fund --no-audit \
    && npm run build

FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY fastapi_app.py ./

COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1
ENV OPENAI_API_KEY=""

EXPOSE 8000

CMD ["uvicorn", "fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"] 