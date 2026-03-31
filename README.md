# AutoState: LLM-Based UML State Machine Generator

AutoState automates the creation of UML State Machines from textual system descriptions using Large Language Models. It uses structured prompting techniques and an automatic F1-score grading system to evaluate output quality.

## Technologies

- **Backend:** Python, FastAPI, Sherpa (LLM task automation)
- **Frontend:** Next.js 16, React 19, Tailwind CSS, shadcn/ui
- **LLM Access:** OpenRouter (unified API for Claude, GPT-4, Llama, etc.)
- **Diagram Parsing:** mermaid-parser-py (sibling dependency)
- **Diagram Rendering:** Mermaid, Graphviz

## Key Features

- UML State Machine generation from natural language descriptions
- Single-prompt and two-stage prompting techniques
- Automatic grading using F1-scores (states, transitions, hierarchical states)
- Interactive web UI with live diagram preview
- Environmental impact tracking (CO2 per run)

## Setup

### Docker (Recommended)

Both repos must be cloned as sibling directories:

```
your-workspace/
├── StateMachineLLM/
└── mermaid-parser-py/
```

```bash
mkdir autostate-workspace && cd autostate-workspace
git clone https://github.com/reheant/StateMachineLLM.git
git clone https://github.com/YOUR-ORG/mermaid-parser-py.git

cd StateMachineLLM
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

docker-compose up --build
```

Open http://localhost:3000 in your browser.

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed instructions and troubleshooting.

---

### Manual Setup

**Prerequisites:** Python 3.11, Node.js 18+, GraphViz

```bash
# Install GraphViz
brew install graphviz          # macOS
sudo apt install graphviz      # Ubuntu/Debian

# Clone both repos as siblings
git clone https://github.com/reheant/StateMachineLLM.git
git clone https://github.com/YOUR-ORG/mermaid-parser-py.git

cd StateMachineLLM
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

# Install Python dependencies
python3 -m pip install -r requirements.txt

# Terminal 1 — backend
uvicorn server:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 in your browser.

See [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md) for API key setup and available models.

---

## Performance Metrics

- States F1-Score: up to 0.94
- Transitions F1-Score: up to 0.69
- Hierarchical States F1-Score: up to 0.67

## License

MIT License

## Contact

Project Link: [https://github.com/reheant/StateMachineLLM](https://github.com/reheant/StateMachineLLM)

Advisor: gunter.mussbacher@mcgill.ca
