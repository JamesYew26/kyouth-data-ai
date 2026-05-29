FROM python:3.14.4-bookworm 

# Copy the modern astral-sh uv binary directly into the image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory inside the container
WORKDIR /app

# Copy configuration and lockfiles first to leverage Docker caching
COPY pyproject.toml uv.lock ./

# Install project dependencies securely without creating a virtualenv
# (or keeping it internal to uv's system management within the container)
RUN uv sync --frozen --no-cache

# Copy the remaining source application code
COPY src/ ./src/

# Strictly defined Entrypoint and CMD to launch via uv run
ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["--app-dir", "src", "--host", "0.0.0.0", "app:app"]