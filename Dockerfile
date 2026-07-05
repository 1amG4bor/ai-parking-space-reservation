# Shared dockerfile for both App UI for users and Admin UI for admins,
# as both are using the same dependencies and only differ in the entry point.


# Use the official uv image for the build stage
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv_setup

# Set up the application environment
WORKDIR /app

# Enable bytecode compilation and specify no-dev for smaller image
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1

# Copy dependency files first for better layer caching
ARG CACHEBUST=3
COPY pyproject.toml uv.lock .env README.md ./
COPY cicd/ ./cicd/
COPY src/ ./src/

# Install dependencies into the system environment to simplify the final image
RUN ls -la
RUN uv sync --no-dev

# Expose Streamlit port
EXPOSE 8501

# Entry point ommitted because this will be overridden in docker-compose for properly handle both UI.
# ENTRYPOINT ["uv", "run", "streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]