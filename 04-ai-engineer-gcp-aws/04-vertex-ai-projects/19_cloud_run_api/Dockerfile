# Imagen para Cloud Run. Se construye desde la carpeta build/ que arma
# preparar_build.sh (app.py + comun/ + requirements.txt + este Dockerfile).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Primero solo requirements: si no cambian, Docker reutiliza esta capa (builds más rápidos).
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# No correr como root: si alguien explota la app, tiene menos poder.
RUN useradd --create-home app && chown -R app /app
USER app

# Cloud Run define PORT (normalmente 8080). "exec" hace que uvicorn reciba las señales de apagado.
CMD exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
