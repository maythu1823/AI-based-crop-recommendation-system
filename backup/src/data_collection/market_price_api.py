import requests
import json
from typing import Dict, Any
import pandas as pd
from datetime import datetime

def get_real_time_market_prices() -> Dict[str, Any]:
    """
    Fetch real-time market prices from the API
    Returns a dictionary with market data
    """
    try:
        # For now, we'll use a mock API endpoint
        # In production, this should be replaced with a real market data API
        response = requests.get("https://api.mockmarketdata.com/prices")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching market prices: {e}")
        return None

def format_market_data(data: Dict) -> pd.DataFrame:
    """
    Format the market data into a DataFrame
    """
    if not data:
        return None
    
    # Create a list of market entries
    market_entries = []
    
    for crop, price_info in data.items():
        market_entries.append({
            'Crop': crop,
            'Current Price (MMK/kg)': price_info.get('current_price', 0),
            'Daily Change (MMK/kg)': price_info.get('daily_change', 0),
            'Trend': 'Rising' if price_info.get('change', 0) > 0 else 'Falling',
            'Last Updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return pd.DataFrame(market_entries)

def get_cached_market_data(cache_file: str) -> pd.DataFrame:
    """
    Get market data from cache if available
    """
    try:
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file)
        return None
    except Exception as e:
        print(f"Error reading cache: {e}")
        return None

def save_market_data(data: pd.DataFrame, cache_file: str) -> None:
    """
    Save market data to cache
    """
    try:
        data.to_csv(cache_file, index=False)
    except Exception as e:
        print(f"Error saving cache: {e}")

if __name__ == "__main__":
    # Test the market data collection
    data = get_real_time_market_prices()
    if data:
        df = format_market_data(data)
        print("\nCurrent Market Prices:")
        print(df)
