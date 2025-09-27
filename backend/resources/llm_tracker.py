class TrackerLLM:
    def __init__(self):
        self.current_llm = "qwen/qwq-32b"  # Default to QwQ-32B (reasoning focused)

    def update_llm(self, response):
        self.current_llm = response

    def print_metrics(self):
        print(self.current_llm)


llm = TrackerLLM()
