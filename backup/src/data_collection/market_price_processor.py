import pandas as pd
from datetime import datetime
import os

def load_market_prices():
    """Load and process the market prices data"""
    try:
        # Get the file path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
        file_path = os.path.join(project_root, "Export Prices.csv")
        
        # Load the data
        df = pd.read_csv(file_path)
        
        # Convert date column to datetime
        df['Price Date'] = pd.to_datetime(df['Price Date'], format='%d/%m/%Y')
        
        # Filter to get only the most recent prices
        latest_date = df['Price Date'].max()
        recent_prices = df[df['Price Date'] == latest_date]
        
        # Clean commodity names
        recent_prices['Commodity'] = recent_prices['Commodity'].str.replace(' (local)', '')
        
        return recent_prices
    except Exception as e:
        print(f"Error loading market prices: {e}")
        return None

def map_region_name(region: str) -> str:
    """Map our region names to WFP Admin 1 names"""
    region_map = {
        'central_plain': 'Mandalay',  # Central Plain includes Mandalay
        'dry_zone': 'Sagaing',       # Dry Zone includes Sagaing
        'delta': 'Yangon',           # Delta region includes Yangon
        'rakhine': 'Rakhine',        # Rakhine state
        'kachin': 'Kachin',          # Kachin state
        'shan': 'Shan',              # Shan state
        'kayin': 'Kayin',            # Kayin state
        'chin': 'Chin',              # Chin state
        'tanintharyi': 'Tanintharyi' # Tanintharyi region
    }
    return region_map.get(region.lower(), region)

def get_region_prices(region: str, df: pd.DataFrame = None) -> pd.DataFrame:
    """Get prices for a specific region"""
    if df is None:
        df = load_market_prices()
        if df is None:
            return None
    
    try:
        # Map our region name to WFP region name
        wfp_region = map_region_name(region)
        
        # Filter by region
        region_prices = df[df['Admin 1'].str.lower() == wfp_region.lower()]
        
        if region_prices.empty:
            return None
            
        # Filter for key commodities (rice, pulses, oil, onions, eggs)
        key_commodities = ['Rice', 'Pulses', 'Oil', 'Onions', 'Eggs', 'Salt']
        region_prices = region_prices[region_prices['Commodity'].str.contains('|'.join(key_commodities), case=False)]
        
        # Group by commodity and get average prices
        grouped = region_prices.groupby('Commodity').agg({
            'Price': 'mean',
            'Unit': 'first',
            'Currency': 'first',
            'Trend': 'first',
            'ALPS Phase': 'first'
        }).reset_index()
        
        # Format the data for display
        grouped['Price'] = grouped['Price'].round(2)
        grouped = grouped.rename(columns={
            'Commodity': 'Crop',
            'Price': 'Current Price',
            'Unit': 'Unit',
            'Currency': 'Currency',
            'Trend': 'Trend',
            'ALPS Phase': 'Market Condition'
        })
        
        # Sort by price
        grouped = grouped.sort_values('Current Price', ascending=False)
        
        return grouped
    except Exception as e:
        print(f"Error getting region prices: {e}")
        return None

def format_market_conditions(condition: str) -> str:
    """Convert ALPS Phase to more user-friendly text"""
    condition_map = {
        'Normal': '✓ Stable',
        'Stress': '⚠️ Caution',
        'Alert': '⚠️ Alert',
        'Crisis': '❌ Crisis'
    }
    return condition_map.get(condition, condition)

if __name__ == "__main__":
    # Test the processor
    df = load_market_prices()
    if df is not None:
        print("\nSample of market prices:")
        print(df.head())
        
        # Test getting region prices
        region = "yangon"  # Example region
        region_prices = get_region_prices(region, df)
        if region_prices is not None:
            print(f"\n\nMarket prices for {region}:")
            print(region_prices)
