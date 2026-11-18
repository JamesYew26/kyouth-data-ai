FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --no-install-project

COPY src ./src

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]
