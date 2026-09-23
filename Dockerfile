FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY templates /app/templates
COPY static /app/static
COPY registry.yaml /app/registry.yaml
COPY scripts /app/scripts
RUN mkdir -p /app/generated

ENV PYTHONPATH=/app
EXPOSE 3050
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=8 CMD curl -fsS http://127.0.0.1:3050/health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3050"]
