# ------------ Front-end build stage ------------
FROM node:18 AS frontend-builder
WORKDIR /app
COPY frontend ./frontend
RUN cd frontend \
    && npm ci --legacy-peer-deps \
    && npm run build

# ------------ Backend stage ------------
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY fastapi_app.py ./

# Copy pre-built frontend assets from previous stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Runtime environment
ENV PYTHONUNBUFFERED=1
ENV OPENAI_API_KEY=""  # Render injects real value at runtime

EXPOSE 8000

CMD ["sh", "-c", "uvicorn fastapi_app:app --host 0.0.0.0 --port ${PORT:-8000}"] 