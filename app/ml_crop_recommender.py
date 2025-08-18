import json
import os
import pandas as pd

# Path to the data sources
CROP_SETTINGS_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'crop_settings.json')
MARKET_PRICES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'crop_prices.csv')

def load_json_data(path):
    """Loads data from a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def load_market_prices(path):
    """Loads and processes market prices from a CSV file."""
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        print(f"Warning: Market price file not found at {path}")
        return None
    except Exception as e:
         print(f"Warning: Could not read market prices. Error: {e}")
         return None


# Load data once when the module is imported
CROP_SETTINGS = load_json_data(CROP_SETTINGS_PATH)
MARKET_PRICES = load_market_prices(MARKET_PRICES_PATH)

def recommend_crops(city: str, greenhouse_size: float, water_availability: float, fertilizer_type: str, weather_data: dict):
    """
    Recommends top crops with yield and profit predictions.
    """
    if not CROP_SETTINGS:
        return []

    city_key = next((key for key in CROP_SETTINGS.keys() if city.lower() in key.lower()), None)
    if not city_key:
        return []
    
    candidate_crops = CROP_SETTINGS.get(city_key, [])
    if not candidate_crops:
        return []

    current_temp = weather_data.get('current', {}).get('temperature_2m', 25.0)
    # Extract current relative humidity in a more robust way. Open-Meteo returns it
    # as an hourly array ("relativehumidity_2m") and our `weather_data` wrapper
    # stores the latest value at the root under "humidity".  Fallback to other
    # common keys before finally defaulting to 70 %.
    current_humidity = (
        weather_data.get('humidity') or
        weather_data.get('current', {}).get('relativehumidity_2m') or  # Open-Meteo key
        weather_data.get('current', {}).get('relative_humidity_2m') or 70.0
    )

    scored_crops = []

    for crop in candidate_crops:
        score = 100
        details = {}
        crop_name_lower = crop['crop_name'].lower()

        # Scoring logic...
        min_temp, max_temp = crop['optimal_temperature']
        temp_match = min_temp <= current_temp <= max_temp
        if not temp_match: score -= 50
        details['temperature'] = {'match': temp_match, 'text': f"Current: {current_temp}°C, Optimal: {min_temp}-{max_temp}°C"}

        water_needed_per_sqm = crop['water_needs_liter_per_day_per_sq_meter']
        total_water_needed = water_needed_per_sqm * greenhouse_size
        water_match = water_availability >= total_water_needed
        if not water_match: score -= 50
        details['water'] = {'match': water_match, 'text': f"Required: {total_water_needed:.1f}L/day, Available: {water_availability}L"}

        size_match, size_text = True, f"Your size: {greenhouse_size}sqm."
        optimal_size_info = crop.get('optimal_greenhouse_size_sq_meter')
        if isinstance(optimal_size_info, list):
            min_size, max_size = optimal_size_info
            size_match = min_size <= greenhouse_size <= max_size
            if not size_match: score -= 15
            size_text += f" Recommended: {min_size}-{max_size}sqm"
        details['size'] = {'match': size_match, 'text': size_text}

        fertilizer_match = fertilizer_type.lower() == crop['fertilizer_preference'].lower()
        if not fertilizer_match: score -= 10
        details['fertilizer'] = {'match': fertilizer_match, 'text': f"Your preference: {fertilizer_type}, Required: {crop['fertilizer_preference']}"}
            
        min_hum, max_hum = crop['optimal_humidity']
        humidity_match = min_hum <= current_humidity <= max_hum
        if not humidity_match: score -= 10
        details['humidity'] = {'match': humidity_match, 'text': f"Current: {current_humidity}%, Optimal: {min_hum}-{max_hum}%"}

        # Yield calculation
        yield_per_sqm = crop.get('yield_per_sq_meter_kg', 0)
        total_yield = yield_per_sqm * greenhouse_size

        # --- Profit Calculation ---
        market_price = 0
        total_revenue = 0
        if MARKET_PRICES is not None and not MARKET_PRICES.empty:
            price_row = MARKET_PRICES[MARKET_PRICES['Crop'].str.strip().str.lower() == crop_name_lower]
            if not price_row.empty:
                market_price = float(price_row['Price_MMK_per_kg'].iloc[0])
                total_revenue = total_yield * market_price
        
        scored_crops.append({
            'crop_name': crop['crop_name'],
            'score': score,
            'yield_per_sqm_kg': round(yield_per_sqm, 2),
            'total_yield_kg': round(total_yield, 2),
            'market_price_mmk': market_price,
            'total_revenue_mmk': round(total_revenue),
            'planting_season': crop.get('planting_season', ['N/A']),
            'details': details
        })

    # Sort and return top 3
    recommended_crops = sorted(scored_crops, key=lambda x: x['score'], reverse=True)
    return recommended_crops[:3]