FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ ./src/

# Install dependencies from pyproject.toml
RUN pip install --no-cache-dir -e .

# Set environment
ENV PYTHONPATH=/app/src

# Run scraper
CMD ["python", "-m", "main"]
