FROM ghcr.io/astral-sh/uv:python3.13-bookworm

WORKDIR /app

# Copy dependency files first for better Docker cache usage
COPY pyproject.toml uv.lock ./

# Install project dependencies
RUN uv sync --frozen

# Copy the project
COPY . .

# Use the virtual environment created by uv
ENV PATH="/app/.venv/bin:$PATH"

# Default command (will be overridden by Docker Compose/Airflow)
CMD ["python", "--version"]