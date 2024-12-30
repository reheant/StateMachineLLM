class TrackerLLM:
    def __init__(self):
        self.current_llm = "openai:gpt-4o"
    
    def update_llm(self, response):
        self.current_llm = response

    def print_metrics(self):
        print(self.current_llm)

llm = TrackerLLM()