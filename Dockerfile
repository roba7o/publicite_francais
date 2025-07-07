FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy requirements first to leverage cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY src /app

# Set Python to look in /app for imports
ENV PYTHONPATH=/app

# Create output directory
RUN mkdir -p /app/output

# Run from the article_scrapers directory
WORKDIR /app/article_scrapers
CMD ["python", "main.py"]