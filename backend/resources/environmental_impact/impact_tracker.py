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
    
    def print_metrics(self):
        print("\nEnvironmental Assessment:")
        print(f"Total Completion Tokens: {self.total_completion_tokens}")
        print(f"Total Carbon Emissions: {self.carbon_emissions} kgCO2eq")
        print(f"Total Energy Use: {self.energy_consumed} kWh")
        print(f"Total Abiotic Resource Use: {self.abiotic_resource_depletion} gSbeq")
        print("\n")

tracker = ImpactTracker()