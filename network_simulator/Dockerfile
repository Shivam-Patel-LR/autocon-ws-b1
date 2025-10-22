FROM python:3.12-slim

# Install system dependencies for geopandas
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/output

# Set environment variable for matplotlib to use non-interactive backend
ENV MPLBACKEND=Agg

# Add src to PYTHONPATH for module imports
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Set default environment variables for container behavior
ENV FORCE_REBUILD=false
ENV SKIP_VERIFICATION=false
ENV GENERATE_SERVICES=true
ENV NUM_SERVICES=100

# Expose API port
EXPOSE 8003

# Default command - run API server
# To run data generation instead, override with: docker run <image> python src/container_init.py
CMD ["python", "-m", "uvicorn", "api.api:app", "--host", "0.0.0.0", "--port", "8003", "--app-dir", "/app/src"]
