# Use the specified python image on Debian Bookworm
FROM python:3.14.4-bookworm

# Set the relocation workspace container path to /app
WORKDIR /app

# Install the uv package manager globally
RUN pip install --no-cache-dir uv

# Copy the dependency management definitions first to leverage Docker layer caching
COPY pyproject.toml ./

# Install project dependencies using uv global system flag
RUN uv pip install --system -r pyproject.toml

# Copy all remaining source files, ensuring nested folders like src/week_2/ map to /app
COPY . .

# Expose the internal port the framework listens on
EXPOSE 8000

# Structured execution layer matching targeted layout adjustments
ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]