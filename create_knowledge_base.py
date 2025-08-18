import pandas as pd
import os
import sys
import json
from tqdm import tqdm

# --- Path Setup ---
# Ensure the script can find the 'app' and 'src' modules
def setup_paths():
    # Get the absolute path of the directory containing the current script
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Add the project root to sys.path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # For debugging purposes, print the paths
    print(f"DEBUG: Project Root: {project_root}")
    print(f"DEBUG: sys.path: {sys.path}")
    
    return project_root

project_root = setup_paths()

# Now, we can import the necessary modules
try:
    from app.profit_predictor import predict_profit
    from app.yield_predictor import predict_yield
    # from app.planting_date_predictor import get_planting_date_recommendations  # No longer needed for static generation
    # from src.data_collection.historical_weather import get_historical_weather_for_region # No longer needed
    from app.crop_info import CropInfo
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure that the 'app' and 'src' directories are in the correct location and are part of the Python path.")
    sys.exit(1)


# --- Configuration & Constants ---
OUTPUT_CSV_PATH = os.path.join(project_root, "knowledge_base.csv")
CROP_TIMELINES_PATH = os.path.join(project_root, "data", "crop_timelines.json")
FULL_DATA_PATH = os.path.join(project_root, "Full Data.txt")

DEFAULT_GREENHOUSE_SIZE = 100  # sq.m
DEFAULT_TEMP = 28  # Celsius
DEFAULT_RAINFALL = 500  # mm -- Annual
DEFAULT_HUMIDITY = 70 # %

REPRESENTATIVE_CITIES = {
    "mandalay": "Mandalay",
    "sagaing": "Sagaing",
    "magway": "Magway",
    "bago": "Bago",
    "yangon": "Yangon",
    "ayeyarwady": "Pathein",
    "naypyitaw": "Naypyidaw",
    "shan": "Taunggyi",
    "kachin": "Myitkyina",
    "chin": "Hakha",
    "rakhine": "Sittwe",
    "kayah": "Loikaw",
    "kayin": "Hpa-An",
    "mon": "Mawlamyine",
    "tanintharyi": "Dawei",
    "delta": "Pathein", 
    "dry_zone": "Magway"
}


# --- Helper Functions ---
def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: JSON file not found at {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from {file_path}")
        return {}

def load_csv_data(file_path, name):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Warning: {name} data file not found at {file_path}")
        return pd.DataFrame()

def parse_price_range(price_str):
    if pd.isna(price_str) or not isinstance(price_str, str):
        return 1000  # Default average price
    try:
        # Remove currency symbols and commas, then split
        parts = price_str.replace('MMK', '').replace(',', '').strip().split('–')
        if len(parts) == 2:
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            return (low + high) / 2
        else:
            return float(parts[0].strip())
    except (ValueError, IndexError):
        return 1000 # Default if parsing fails

def parse_yield_value(yield_str):
    if pd.isna(yield_str):
        return None # Return None if data is missing
    try:
        return float(yield_str)
    except (ValueError, TypeError):
        return None # Return None if parsing fails

def main():
    print("Starting knowledge base creation using 'Full Data.txt'...")
    
    # Load external data
    crop_timelines = load_json(CROP_TIMELINES_PATH)
    full_data_df = load_csv_data(FULL_DATA_PATH, "Full Data")
    crop_info_manager = CropInfo()


    if full_data_df.empty:
        print("Critical error: 'Full Data.txt' could not be loaded or is empty. Aborting.")
        return

    # --- Data Correction ---
    # Conditionally replace placeholder 'Township' values
    if 'Township' in full_data_df.columns and 'Region' in full_data_df.columns:
        # Only replace if the township is a placeholder like 'Township_1', 'Township_2', etc.
        # Keep legitimate township names.
        full_data_df['Township'] = full_data_df.apply(
            lambda row: row['Region'] if str(row['Township']).strip().startswith('Township_') else row['Township'],
            axis=1
        )
        print("Conditionally replaced placeholder 'Township' values with 'Region' values.")
    else:
        print("Error: Required columns ('Township', 'Region') not found in 'Full Data.txt'.")
        return
        
    # Clean column names just in case
    full_data_df.columns = full_data_df.columns.str.strip()

    all_crops_data = []

    # Use tqdm for a progress bar
    for _, row in tqdm(full_data_df.iterrows(), total=full_data_df.shape[0], desc="Processing Regions"):
        region_name = row.get("Region", "Unknown")
        township_name = row.get("Township", "Unknown")
        lat = row.get("Latitude")
        lon = row.get("Longitude")
        
        # Some rows might have a single crop, some a list
        suitable_crops_str = row.get("Suitable Crops", "")
        if pd.isna(suitable_crops_str):
            suitable_crops = []
        else:
            suitable_crops = [crop.strip() for crop in suitable_crops_str.split(',')]
        
        avg_price = parse_price_range(row.get("Average Market Price (MMK/kg)"))
        base_yield = parse_yield_value(row.get("Yield (kg/sqm)"))

        for crop_name in suitable_crops:
            # The crop name from Full Data.txt is the display name
            crop_name_display = crop_name.strip()

            # --- Predictions (without historical weather) ---
            yield_data = predict_yield(
                crop_name=crop_name_display,
                temperature=DEFAULT_TEMP, 
                rainfall=DEFAULT_RAINFALL,
                humidity=DEFAULT_HUMIDITY,
                greenhouse_size=DEFAULT_GREENHOUSE_SIZE,
                base_yield_kg_per_sqm=base_yield
            )
            
            profit_data = predict_profit(
                crop_name=crop_name_display,
                yield_per_sqm=yield_data['yield_per_sqm'],
                total_yield=yield_data['total_yield'],
                price_per_kg=avg_price,
                greenhouse_size=DEFAULT_GREENHOUSE_SIZE
            )

            # Get additional details from CropInfo
            additional_info = crop_info_manager.get_crop_info(crop_name_display)
            planting_season = crop_timelines.get(crop_name_display, {}).get("Planting", "Not available")

            record = {
                "CropName": crop_name_display,
                "KnownTownships": township_name,
                "KnownRegions": region_name,
                "Latitude": lat,
                "Longitude": lon,
                "BaseYieldKgPerSqm": base_yield,
                "AvgMarketPriceMMK": avg_price,
                "PlantingSeason": planting_season,
                "HarvestingSeason": crop_timelines.get(crop_name_display, {}).get("Harvesting", "Not available"),
                "PredictedYieldPerSqmKg": yield_data.get('yield_per_sqm'),
                "PredictedTotalYieldKg": yield_data.get('total_yield'),
                "PredictedRevenueMMK": profit_data.get('total_revenue'),
                "PredictedWaterCostMMK": profit_data.get('total_water_cost'),
                "PredictedLaborCostMMK": profit_data.get('labor_cost'),
                "PredictedFertilizerCostMMK": profit_data.get('fertilizer_cost'),
                "PredictedProfitMMK": profit_data.get('total_profit'),
                "PlantingRecommendation": f"General season: {planting_season}",
                "PlantingRationale": "Based on general regional suitability and crop timelines.",
                "CareInfo": additional_info.get('care_info'),
                "MarketInfo": additional_info.get('market_info'),
                "Summary": additional_info.get('summary')
            }
            all_crops_data.append(record)

    # Create the final DataFrame and save it
    if all_crops_data:
        final_df = pd.DataFrame(all_crops_data)
        # Create lowercase columns for easier matching
        final_df['KnownTownships_lower'] = final_df['KnownTownships'].str.lower()
        final_df['KnownRegions_lower'] = final_df['KnownRegions'].str.lower()
        final_df.to_csv(OUTPUT_CSV_PATH, index=False, encoding='utf-8')
        print(f"Successfully created knowledge base at: {OUTPUT_CSV_PATH}")
    else:
        print("No data was processed to generate the knowledge base.")


if __name__ == "__main__":
    main() 