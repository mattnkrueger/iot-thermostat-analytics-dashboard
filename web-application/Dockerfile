FROM python:3.12-slim-bookworm
WORKDIR /dash_app

COPY real-time-thermostat-analytics-dashboard-web-application/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*

COPY real-time-thermostat-analytics-dashboard-postgres-orm ./src/db
COPY real-time-thermostat-analytics-dashboard-web-application/src ./src

CMD ["python", "src/app.py"]
# CMD ["python", "-u", "src/app.py"]
