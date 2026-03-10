import pandas as pd
import os
import yaml

def calculate_aggregated_usage():
    """
    Calculates and prints the aggregated token usage and cost per prompt.
    """
    # Load usage path from config
    usage_path = "data/usage.csv" # Default
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'token_usage_path' in config:
                    usage_path = config['token_usage_path']
        except Exception as e:
            print(f"Error reading config for usage path: {e}")
            
    if not os.path.exists(usage_path):
        print(f"Usage file not found at: {usage_path}")
        return

    try:
        usage_df = pd.read_csv(usage_path)
    except Exception as e:
        print(f"Error reading usage file: {e}")
        return

    # Group by prompt and aggregate
    aggregated_usage = usage_df.groupby('prompt').agg({
        'input_token_count': 'sum',
        'output_token_count': 'sum',
        'price': 'sum'
    }).reset_index()

    print("Aggregated Token Usage per Prompt:")
    print(aggregated_usage)

if __name__ == "__main__":
    calculate_aggregated_usage()
