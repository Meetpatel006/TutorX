FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && \
    uv pip install --no-cache -e .

# Copy application code
COPY main.py .
COPY client.py .
COPY utils/ ./utils/

# Expose port for MCP server
EXPOSE 8000

# Run MCP server
CMD ["python", "main.py"]
