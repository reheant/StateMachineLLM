# AutoState: State Machine-Driven LLM Framework for UML Modeling Automation

## Library Overview

This library aims to automate the creation of UML State Machines using Large Language Models (LLMs) through an innovative State Machine Framework (SMF). The primary goal is to streamline the model-driven engineering process by reducing the time and expertise required to generate accurate UML state machines from textual system descriptions.

## Motivation

Traditional methods of creating state machines using LLMs often suffer from:
- Hallucinations and inaccurate modeling
- Lack of structured approach to complex modeling tasks
- Time-consuming and expertise-intensive processes

Our solution embeds a state machine within the LLM decision-making process to:
- Reduce hallucinations
- Break down complex tasks into manageable subtasks
- Provide a more structured approach to software modeling

## Technologies Used

- **Programming Languages:** 
  - Python

- **Libraries and Frameworks:**
  - Sherpa (LLM task automation library)
  - Chainlit (Web UI framework)
  - AI suite (Unified interface to multiple Generative AI providers.)
  - Mermaid (Diagram generation)

- **Development Tools:**
  - VSCode

## Key Features

- Automated UML State Machine Generation
- Multiple Prompting Techniques
  - Zero-shot
  - One-shot
  - Two-shot
  - Three-shot
  - Chain-of-Thought Prompting
- Interactive Web UI
- Customizable State Machine Generation
- Performance Evaluation using F1-Scores

## Installation and Setup

### Prerequisites

- Python 3.8+
- API Key for the LLM you will use

### Setup

```bash
# Clone the repository
git clone https://github.com/ECSE458-Multi-Agent-LLM/llm

# Verify Python is installed
python3 --version
pip --version

# Enter the directory
cd llm

# Download dependencies
pip install -r requirements.txt

# Configure virtual environment
mv .env.example to .env
export OPENAI_API_KEY='your-api-key'

# Launch UI
chainlit run app.py -w
```

### Frontend Setup

After completing the setup, launch http://localhost:8000 in your browser


## Usage

```python
# change the description to your use case in event_driven_smf.py or simple_linear_smf.py
description = desired description
if __name__ == "__main__":
    run_simple_linear_smf() # or run_event_driven_smf() 
# Choose your required LLM in the terminal
```

## Performance Metrics

Our framework has achieved:
- States F1-Score: Up to 0.94
- Transitions F1-Score: Up to 0.69
- Hierarchical States F1-Score: Up to 0.67

## Ethical Considerations

We are committed to:
- Minimizing bias in generated models
- Ensuring transparency in AI-generated outputs
- Providing clear documentation of generation processes
- Creating an assistive tool, not a replacement for human engineering

## License

MIT License

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact

Project Link: [https://github.com/ECSE458-Multi-Agent-LLM/llm](https://github.com/ECSE458-Multi-Agent-LLM/llm)

Advisor: gunter.mussbacher@mcgill.ca
