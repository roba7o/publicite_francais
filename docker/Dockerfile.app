FROM python:3.12-slim-bullseye

# Upgrade OS packages (optional in dev, but fine here)
RUN apt-get update && apt-get upgrade -y && apt-get clean

# Prevent .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working dir to src
WORKDIR /app/src

# Copy pyproject.toml first (leverage layer cache)
COPY pyproject.toml /app/

# Install dependencies
RUN pip install --no-cache-dir /app

# Tell Python to treat /app/src as a root for imports
ENV PYTHONPATH=/app/src

# In dev, the code is volume-mounted, so we don't COPY src/

# Run your package as a module
CMD ["python", "-m", "article_scrapers.main"]
