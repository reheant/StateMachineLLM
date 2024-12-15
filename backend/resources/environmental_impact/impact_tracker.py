class ImpactTracker:
    def __init__(self):
        self.energy_consumed = 0
        self.carbon_emissions = 0
        self.abiotic_resource_depletion = 0
        self.total_completion_tokens = 0
    
    def update_impacts(self, response):
        self.energy_consumed += response.impacts.energy.value
        self.carbon_emissions += response.impacts.gwp.value
        self.abiotic_resource_depletion += response.impacts.adpe.value
        self.total_completion_tokens += response.usage.completion_tokens
    
    def get_metrics(self):
        return {
            "energy_consumed": self.energy_consumed,
            "carbon_emissions": self.carbon_emissions,
            "abiotic_resource_depletion": self.abiotic_resource_depletion,
            "completion_tokens": self.total_completion_tokens,
        }

tracker = ImpactTracker()