# Use an official lightweight Python image
FROM python:3.13-slim

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Disables automatic opening in local browser tab and
# prevents streamlit from gathering usage stats to avoid
# extra network use
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false


# Set a non-root working directory
WORKDIR /app

RUN mkdir /app/saved_articles

ENV SAVE_ARTICLES_PATH=/app/saved_articles

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache layers
COPY requirements.txt .

# Install Python application dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Configure the default executable configuration
COPY docker-entrypoint.sh /usr/local/bin/
RUN sed -i "s/\r$//" /usr/local/bin/docker-entrypoint.sh && \
    chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Create a non-root user and grant permissions for security
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser && \
    chown -R appuser:appgroup /app
USER appuser

# Expose Streamlit's default network port
EXPOSE 8501

# Define a container health check targeting the internal Streamlit endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health').read()" || exit 1