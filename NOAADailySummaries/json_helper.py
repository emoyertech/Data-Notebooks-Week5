import json
import pandas as pd
import os
from pathlib import Path

def load_json_files_to_dataframe(directory_path=None):
    """
    Load all JSON files from a directory into a pandas DataFrame.
    
    Args:
        directory_path: Path to directory containing JSON files.
                       If None, uses ./data/daily_summaries/
    
    Returns:
        pandas.DataFrame: DataFrame containing all JSON data flattened
    """
    if directory_path is None:
        directory_path = Path(__file__).parent / 'data' / 'daily_summaries'
    
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    all_data = []
    
    # Find all JSON files
    json_files = list(directory_path.glob('*.json'))
    
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {directory_path}")
    
    print(f"Found {len(json_files)} JSON files")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                
            # Handle both single object and array of objects
            if isinstance(data, list):
                all_data.extend(data)
            elif isinstance(data, dict):
                # If dict has a 'results' key with list data, use that
                if 'results' in data and isinstance(data['results'], list):
                    all_data.extend(data['results'])
                else:
                    all_data.append(data)
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse {json_file}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No data found in JSON files")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    print(f"Loaded {len(df)} records into DataFrame")
    return df
