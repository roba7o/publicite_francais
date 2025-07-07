FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Add article_scrapers to Python path
ENV PYTHONPATH="${PYTHONPATH}:/app/article_scrapers"

RUN mkdir -p /app/output

CMD ["python", "-m", "article_scrapers.main"]