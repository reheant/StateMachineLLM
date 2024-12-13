import pandas as pd
from ecologits.impacts.llm import compute_llm_impacts

def parse_token_usage(file_path):
    try:
        df = pd.read_csv(file_path)
        total_generated_tokens = df['n_generated_tokens_total'].sum()

        all_stats = []
        for _, row in df.iterrows():
            model_name = row['model']
            
            active_params = None
            total_params = None
            
            if 'gpt-4o-' in model_name:
                active_params = 220
                total_params = 440
            elif 'gpt-4-' in model_name:
                active_params = 880
                total_params = 1760
            elif 'gpt-3.5-' in model_name:
                active_params = 70
                total_params = 70
            
            if active_params is None or total_params is None:
                continue
                
            row_stats = compute_llm_impacts(
                model_active_parameter_count=active_params,
                model_total_parameter_count=total_params,
                output_token_count=row['n_generated_tokens_total'],
                if_electricity_mix_adpe=7.37708e-8,
                if_electricity_mix_pe=9.988,
                if_electricity_mix_gwp=0.590478
            )

            all_stats.append(row_stats)
        
        if not all_stats:
            return {
                'total_generated_tokens': total_generated_tokens,
                'carbon_emissions': 0,
                'energy_use': 0,
                'abiotic_resources': 0
            }
        
        total_carbon = sum(stat.gwp.value for stat in all_stats)
        total_energy = sum(stat.energy.value for stat in all_stats)
        total_abiotic = sum(stat.adpe.value for stat in all_stats)
        
        stats = {
            'total_generated_tokens': total_generated_tokens,
            'carbon_emissions': total_carbon,
            'energy_use': total_energy,
            'abiotic_resources': total_abiotic * 1000
        }
        
        return stats
    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None

def main():
    path = """C:\\Users\\alect\\dev\\llm\\backend\\resources\\environmental_impact\\activity-2024-10-01-2025-01-01.csv"""
    stats = parse_token_usage(path)
    
    print(f"Total Generated Tokens: {stats['total_generated_tokens']:,}")
    print(f"Carbon Emissions: {stats['carbon_emissions']:.2f} kgCO2eq")
    print(f"Energy Use: {stats['energy_use']:.2f} kWh")
    print(f"Abiotic Resource Use: {stats['abiotic_resources']:.2f} gSbeq")

if __name__ == "__main__":
    main()