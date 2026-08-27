# Dockerfile — single-process build for hosts that expect one container
# (e.g. Hugging Face Spaces' Docker SDK, which looks for a file named
# exactly "Dockerfile"). This runs the Streamlit frontend only, which is
# self-contained (it calls the agent in-process, not over HTTP) — the
# separate FastAPI backend (Dockerfile.backend) is optional and only
# needed if you want a standalone health-check/API endpoint alongside it.
#
# For local multi-container development, use docker-compose.yml instead,
# which builds Dockerfile.backend and Dockerfile.frontend separately.

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY frontend/ ./frontend/
COPY data/ ./data/

RUN python -m app.db.init_db
RUN mkdir -p /app/chroma_db

# Hugging Face Spaces' Docker SDK defaults to port 7860.
# If deploying elsewhere, change this and the matching platform config.
EXPOSE 7860

CMD ["streamlit", "run", "frontend/streamlit_app.py", \
     "--server.port=7860", "--server.address=0.0.0.0", "--server.headless=true"]
