# Single-stage image: gunicorn serves the app, WhiteNoise serves the static
# files collected at build time, so nothing else (nginx, a CDN) is required
# in front of this container on an intranet deployment. See
# docs/DEPLOYMENT.md for how to run it and what env vars it needs.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False

WORKDIR /app

RUN groupadd --system app && useradd --system --gid app --home-dir /app app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Needs *a* DJANGO_SECRET_KEY to boot (the insecure dev default from
# settings.py is fine here, no request handling happens during a build) —
# the real one is supplied at container runtime, never baked into the image.
RUN python manage.py collectstatic --noinput

RUN chown -R app:app /app
USER app

EXPOSE 8000

# Applies migrations on every start (a no-op once the DB is up to date) so
# the image is self-sufficient on a fresh volume with no manual step.
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"]
