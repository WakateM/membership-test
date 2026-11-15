# Shared base: Python plus the server's dependencies.
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /service
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

# Test stage: build with --target test; the build fails if any test fails.
FROM base AS test
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY tests ./tests
RUN python -m pytest -v -s --color=yes
CMD ["python", "-m", "pytest", "-v", "-s", "--color=yes", "-p", "no:warnings"]

# Server stage (default target). The database lives in /tmp inside the container,
# with no volume, so every new container starts with an empty database.
FROM base AS server
ENV DATABASE_PATH=/tmp/server.sqlite3
EXPOSE 8080
CMD ["uvicorn", "app.main:application", "--host", "0.0.0.0", "--port", "8080"]
