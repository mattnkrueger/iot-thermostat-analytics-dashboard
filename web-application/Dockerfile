FROM python:3.12-slim-bookworm
WORKDIR /dash_app

COPY web-application/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY postgres-orm ./src/db
COPY web-application/src ./src

CMD ["python", "src/app.py"]
# CMD ["python", "-u", "src/app.py"]
