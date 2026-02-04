# Docker Setup Guide for StateMachineLLM

This guide will help your teammates run the project using Docker, eliminating "it's not working on my machine" issues.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS/Windows) or Docker Engine (Linux)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

## Important: Multi-Repository Setup

This project depends on the `mermaid-parser-py` repository. Both repos must be cloned as sibling directories:

```
your-workspace/
├── StateMachineLLM/          # This repo
└── mermaid-parser-py/        # Dependency repo
```

## Quick Start

### 1. Clone Both Repositories

```bash
# Create a workspace directory
mkdir autostate-workspace
cd autostate-workspace

# Clone the main repository
git clone https://github.com/reheant/StateMachineLLM.git

# Clone the mermaid-parser dependency (as a sibling)
git clone https://github.com/YOUR-ORG/mermaid-parser-py.git

# Verify structure
ls
# Should show: StateMachineLLM/  mermaid-parser-py/
```

### 2. Configure Environment Variables

```bash
cd StateMachineLLM
cp .env.example .env
```

Then edit `.env` and add your API keys:

```env
OPENROUTER_API_KEY=your_actual_api_key_here
OPENAI_API_KEY=your_actual_api_key_here
```

### 3. Build and Run with Docker Compose

```bash
# From the StateMachineLLM directory
docker-compose up --build
```

This will:
- Build the Docker image with all dependencies (including mermaid-parser-py)
- Start the application
- Expose it on http://localhost:8000

### 4. Access the Application

Open your browser and navigate to:
```
http://localhost:8000
```

## Common Commands

### Start the application (after first build)
```bash
docker-compose up
```

### Start in detached mode (runs in background)
```bash
docker-compose up -d
```

### Stop the application
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up --build
```

### View logs
```bash
docker-compose logs -f
```

### Stop and remove all containers, networks, and volumes
```bash
docker-compose down -v
```

## Using Docker without Docker Compose

If you prefer to use Docker directly:

### Build the image
```bash
# Run from StateMachineLLM directory
docker build -t statemachine-llm -f Dockerfile ..
```

### Run the container
```bash
docker run -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/backend/resources/event_driven_log:/app/backend/resources/event_driven_log \
  -v $(pwd)/backend/resources/single_prompt_outputs:/app/backend/resources/single_prompt_outputs \
  statemachine-llm
```

## Troubleshooting

### "Cannot find mermaid-parser-py"
Make sure both repositories are cloned as sibling directories:
```bash
cd ..
ls
# Should show both: StateMachineLLM/  mermaid-parser-py/
```

### Port 8000 is already in use
If you get a port conflict error:

1. Stop any other services using port 8000
2. Or change the port mapping in `docker-compose.yml`:
   ```yaml
   ports:
     - "8080:8000"  # Use port 8080 on your machine instead
   ```

### Permission issues with volumes
On Linux, you might need to adjust permissions:
```bash
sudo chown -R $USER:$USER backend/resources/
```

### Container fails to start
Check the logs:
```bash
docker-compose logs
```

### API keys not working
Ensure your `.env` file is in the correct location:
```bash
ls -la .env
# Should be in StateMachineLLM/.env
```

### Need to reset everything
```bash
docker-compose down -v
docker system prune -a
docker-compose up --build
```

## Development Tips

### For active development

If you want to make code changes without rebuilding:

1. Add a volume mount for live code updates in `docker-compose.yml`:
   ```yaml
   volumes:
     - .:/app
   ```

2. The Chainlit `-w` flag enables auto-reload on file changes

### Running tests in Docker

Execute tests inside the running container:
```bash
docker-compose exec statemachine-llm python tests/run_all_tests.py
```

### Interactive shell access

Get a shell inside the container:
```bash
docker-compose exec statemachine-llm /bin/bash
```

## What Docker Solves

✅ **Consistent Python version** (3.11)  
✅ **All system dependencies** (graphviz, etc.)  
✅ **Python package versions** locked  
✅ **Cross-platform compatibility** (macOS, Windows, Linux)  
✅ **No virtual environment management needed**  
✅ **Isolated from system Python**  
✅ **Handles multi-repo dependencies** (mermaid-parser-py)

## System Requirements

- **Disk Space:** ~2GB for Docker image
- **RAM:** 2GB minimum, 4GB recommended
- **CPU:** Any modern multi-core processor

## Repository Structure

When properly set up, your workspace should look like:

```
your-workspace/
├── StateMachineLLM/
│   ├── .env                    # Your API keys (create from .env.example)
│   ├── Dockerfile              # Docker image definition
│   ├── docker-compose.yml      # Orchestration config
│   ├── app.py                  # Main application
│   ├── requirements.txt        # Python dependencies (includes -e ../mermaid-parser-py)
│   └── backend/
└── mermaid-parser-py/          # Sibling dependency repository
    ├── mermaid_parser/
    └── pyproject.toml
```

## Next Steps

After Docker is working, your teammates can:
1. Focus on using the application
2. Contribute code without environment setup issues
3. Deploy to cloud services that support Docker
4. Scale the application using container orchestration

## Support

If you encounter issues:
1. Check Docker is running: `docker --version`
2. Verify Docker Compose: `docker-compose --version`
3. Ensure both repos are cloned: `ls ../mermaid-parser-py`
4. Review logs: `docker-compose logs`
5. See the main [README.md](README.md) for project details
