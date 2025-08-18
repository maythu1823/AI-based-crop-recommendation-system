import pandas as pd
from datetime import datetime
import os

def get_latest_market_prices(region: str) -> pd.DataFrame:
    """
    Get the latest market prices for a specific region
    """
    # Load market prices data
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    file_path = os.path.join(project_root, "data", "market_prices.csv")
    
    try:
        df = pd.read_csv(file_path)
        
        # Filter by region
        region_df = df[df['region'] == region]
        
        # Get latest date
        latest_date = region_df['date'].max()
        
        # Get latest prices
        latest_prices = region_df[region_df['date'] == latest_date]
        
        # Format the data
        market_data = []
        for _, row in latest_prices.iterrows():
            market_data.append({
                'Crop': row['crop_name'],
                'Current Price (MMK/kg)': row['price_per_kg'],
                'Daily Change (MMK/kg)': 0,  # We'll calculate this later
                'Trend': 'Stable'  # We'll update this later
            })
        
        return pd.DataFrame(market_data)
        
    except Exception as e:
        print(f"Error getting market prices: {e}")
        return None

def calculate_price_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate price changes and trends
    """
    if df is None or len(df) == 0:
        return df
    
    # Sort by crop name
    df = df.sort_values('Crop')
    
    # Calculate price changes (for now, we'll just show 0)
    # In a real implementation, we would compare with previous day's prices
    df['Daily Change (MMK/kg)'] = 0
    df['Trend'] = 'Stable'
    
    return df

if __name__ == "__main__":
    # Example usage
    region = "yangon"  # or any other region
    df = get_latest_market_prices(region)
    if df is not None:
        df = calculate_price_changes(df)
        print("\nLatest Market Prices:")
        print(df)
