# Use Python 3.11 as specified in README
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js for mermaid-parser-py
RUN apt-get update && apt-get install -y \
    graphviz \
    git \
    build-essential \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy mermaid-parser-py package first (from parent directory)
COPY mermaid-parser-py/ /app/mermaid-parser-py/

# Install mermaid-parser-py in editable mode
RUN pip install --no-cache-dir -e /app/mermaid-parser-py/

# Copy StateMachineLLM requirements
COPY StateMachineLLM/requirements.txt /app/requirements.txt

# Install other Python dependencies (skip the mermaid-parser line)
RUN grep -v "mermaid-parser-py" requirements.txt > requirements_docker.txt && \
    pip install --no-cache-dir -r requirements_docker.txt

# Copy the rest of the StateMachineLLM application
COPY StateMachineLLM/ /app/

# Create necessary directories
RUN mkdir -p /app/.chainlit \
    /app/.files \
    /app/backend/resources/event_driven_log \
    /app/backend/resources/single_prompt_log \
    /app/backend/resources/single_prompt_outputs

# Expose Chainlit default port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["chainlit", "run", "app.py", "-w", "--host", "0.0.0.0", "--port", "8000"]
