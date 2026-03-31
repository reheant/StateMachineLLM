# OpenRouter Setup

The backend uses OpenRouter to access LLMs, giving you a single API key for Claude, GPT-4, Llama, and more.

## Setup Instructions

1. **Install GraphViz (Required for Diagram Generation):**
   
   **macOS:**
   ```bash
   brew install graphviz
   ```
   
   **Ubuntu/Debian:**
   ```bash
   sudo apt install graphviz
   ```
   
   **Windows:**
   - Download from [GraphViz website](https://graphviz.org/download/)
   - Or use chocolatey: `choco install graphviz`
   
   **Verify installation:**
   ```bash
   which dot
   dot -V
   ```

2. **Install Python Dependencies:**
   ```bash
   pip3 install requests
   ```

3. **Get an OpenRouter API Key:**
   - Go to [OpenRouter](https://openrouter.ai/)
   - Sign up and get your API key

4. **Set Environment Variable:**
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```

   Or add it to your `.env` file:
   ```
   OPENROUTER_API_KEY=your_api_key_here
   ```

5. **Available Models:**
   The default model is `anthropic/claude-3.5-sonnet`, but you can modify the model parameter in the `process_umple_attempt_openrouter` function in `single_prompt.py`.

   Popular models available through OpenRouter:
   - `anthropic/claude-3.5-sonnet`
   - `openai/gpt-4o`
   - `openai/gpt-4o-mini`
   - `meta-llama/llama-3.2-3b-instruct`
   - `google/gemini-pro-1.5`

6. **Start the backend:**
   ```bash
   uvicorn server:app --reload --port 8000
   ```

## Notes

- OpenRouter provides unified access to multiple AI models through a single API
- Billing is handled through OpenRouter's pricing structure