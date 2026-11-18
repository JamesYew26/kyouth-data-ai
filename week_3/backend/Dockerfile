# Build context is the repository root (see docker-compose.yaml) so the image can
# include the shared week_2 modules instead of keeping a copy-pasted duplicate.
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies first: this layer is cached until pyproject/uv.lock change.
COPY week_3/backend/pyproject.toml week_3/backend/uv.lock ./
RUN uv sync --no-dev --no-install-project

# Application code: the API plus the shared week_2 logic.
COPY week_2/prompt_model.py week_2/find_skill_gaps.py ./src/
COPY week_3/backend/src/app.py ./src/

# Run as an unprivileged user.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]
