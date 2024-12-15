import pandas as pd
import os
from ecologits.impacts.llm import compute_llm_impacts
from collections import defaultdict

def parse_token_usage(file_path):
    try:
        df = pd.read_csv(file_path)
        
        # Initialize defaultdict to store stats by model
        model_stats = defaultdict(lambda: {
            'total_generated_tokens': 0,
            'carbon_emissions': 0,
            'energy_use': 0,
            'abiotic_resources': 0
        })
        
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
                
            stats = compute_llm_impacts(
                model_active_parameter_count=active_params,
                model_total_parameter_count=total_params,
                output_token_count=row['n_generated_tokens_total'],
                if_electricity_mix_adpe=7.37708e-8,
                if_electricity_mix_pe=9.988,
                if_electricity_mix_gwp=0.590478
            )
            
            # Update stats for this model
            model_stats[model_name]['total_generated_tokens'] += row['n_generated_tokens_total']
            model_stats[model_name]['carbon_emissions'] += stats.gwp.value
            model_stats[model_name]['energy_use'] += stats.energy.value
            model_stats[model_name]['abiotic_resources'] += stats.adpe.value * 1000
        
        # Calculate totals across all models
        total_stats = {
            'total_generated_tokens': sum(stats['total_generated_tokens'] for stats in model_stats.values()),
            'carbon_emissions': sum(stats['carbon_emissions'] for stats in model_stats.values()),
            'energy_use': sum(stats['energy_use'] for stats in model_stats.values()),
            'abiotic_resources': sum(stats['abiotic_resources'] for stats in model_stats.values())
        }
        
        return model_stats, total_stats
    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return None, None
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return None, None

def main():
    script_dir = os.path.dirname(__file__)
    csv_path = "./activity-2024-10-01-2025-01-01.csv"
    path = os.path.join(script_dir, csv_path)
    model_stats, total_stats = parse_token_usage(path)
    
    if model_stats and total_stats:
        print("\nStats by Model:")
        print("-" * 50)
        for model, stats in model_stats.items():
            print(f"\nModel: {model}")
            print(f"Generated Tokens: {stats['total_generated_tokens']:,}")
            print(f"Carbon Emissions: {stats['carbon_emissions']:.2f} kgCO2eq")
            print(f"Energy Use: {stats['energy_use']:.2f} kWh")
            print(f"Abiotic Resource Use: {stats['abiotic_resources']:.2f} gSbeq")
        
        print("\nTotal Stats Across All Models:")
        print("-" * 50)
        print(f"Total Generated Tokens: {total_stats['total_generated_tokens']:,}")
        print(f"Total Carbon Emissions: {total_stats['carbon_emissions']:.2f} kgCO2eq")
        print(f"Total Energy Use: {total_stats['energy_use']:.2f} kWh")
        print(f"Total Abiotic Resource Use: {total_stats['abiotic_resources']:.2f} gSbeq")

if __name__ == "__main__":
    main()