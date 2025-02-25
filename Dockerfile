# Use Python 3.10 as base image (to meet autogen-ext 0.4.7 requirements)
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.4.2 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="$POETRY_HOME/bin:$PATH"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies with pip - ensure all packages are installed properly
RUN pip install --upgrade pip && \
    # Install packages separately to avoid version conflicts
    pip install --no-cache-dir anthropic>=0.8.0 && \
    pip install --no-cache-dir autogen-ext==0.4.7 && \
    # Install other dependencies from requirements
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir tenacity>=8.2.3

# Copy project files
COPY . .

# Install the package in development mode and Playwright
RUN pip install -e . && \
    playwright install --with-deps chromium

# Expose port for FastAPI
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "magnetic.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 