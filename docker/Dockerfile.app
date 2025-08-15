FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy pyproject.toml and source directory
COPY pyproject.toml .
COPY src/ ./src/

# Install Python packages
RUN pip install --no-cache-dir -e .

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Health check to ensure the app can start
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); from main import main; print('App health: OK')" || exit 1

# Default command - run the main scraper
CMD ["python", "-m", "main"]