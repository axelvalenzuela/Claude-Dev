# Minimal image for Cloud Run. No multi-stage build needed: this app has
# no compiled dependencies and no build step (the frontend is plain
# HTML/CSS/JS, served as static files by FastAPI itself).
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first, separately from the app code, so Docker's
# layer cache skips this step on every rebuild that only touches src/.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# data/docs/ ships inside the image; data/index/ does NOT (.dockerignore
# below) — it's built on first startup by src/main.py's lifespan hook,
# using whatever GCP credentials the Cloud Run service account provides.
COPY src/ ./src/
COPY web/ ./web/
COPY data/docs/ ./data/docs/

# Cloud Run injects PORT (usually 8080) and expects the container to
# listen on it. src/config.py reads the same PORT env var, so this stays
# correct even if Cloud Run ever changes the default.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT}"]
