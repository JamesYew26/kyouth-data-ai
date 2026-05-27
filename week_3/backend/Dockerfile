# Use the specified python 3.14 image on Debian Bookworm
FROM python:3.14.4-bookworm

# Set the working directory inside the container
WORKDIR /backend

# Install uv package manager globally
RUN pip install --no-cache-dir uv

# Copy dependency files first to leverage Docker caching layers
COPY pyproject.toml ./

# Install project dependencies using uv (creates a virtual environment implicitly or syncs)
RUN uv pip install --system -r pyproject.toml

# Copy the rest of the application code into the container
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Set entrypoint and default arguments as requested
ENTRYPOINT ["uv", "run", "uvicorn"]
CMD ["--app-dir", "src", "--host", "0.0.0.0", "--port", "8000", "app:app"]