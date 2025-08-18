def fmt(val, unit="", decimals=1):
    """Format a value with a unit and a given number of decimals."""
    try:
        if val is None or val == "N/A":
            return "N/A"
        val = float(val)
        if decimals == 0:
            return f"{int(round(val))}{unit}"
        return f"{val:.{decimals}f}{unit}"
    except Exception:
        return "N/A"

import os
import sys

# Add project root and src directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'src', 'market_predictor'))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
from market_predictor import MarketPricePredictor
from data_collection.weather import get_city_coordinates, get_open_meteo_weather
from utils.weather_utils import calculate_sunlight_hours, get_weather_metrics
from app.market_prices_display import show_market_prices

def get_weather_condition(weather_code):
    """Convert WMO weather code to human-readable condition with emoji"""
    weather_conditions = {
        0: "☀️ Clear Sky",
        1: "🌤️ Mainly Clear",
        2: "⛅ Partly Cloudy",
        3: "☁️ Overcast",
        45: "🌫️ Fog",
        48: "❄️ Rime Fog",
        51: "🌧️ Light Drizzle",
        53: "🌧️ Moderate Drizzle",
        55: "🌧️ Dense Drizzle",
        56: "🌨️ Light Freezing Drizzle",
        57: "🌨️ Dense Freezing Drizzle",
        61: "🌧️ Slight Rain",
        63: "🌧️ Moderate Rain",
        65: "🌧️ Heavy Rain",
        66: "🌨️ Light Freezing Rain",
        67: "🌨️ Heavy Freezing Rain",
        71: "🌨️ Slight Snow",
        73: "🌨️ Moderate Snow",
        75: "🌨️ Heavy Snow",
        77: "🌨️ Snow Grains",
        80: "🌧️ Slight Rain Showers",
        81: "🌧️ Moderate Rain Showers",
        82: "🌧️ Violent Rain Showers",
        85: "🌨️ Slight Snow Showers",
        86: "🌨️ Heavy Snow Showers",
        95: "⚡ Thunderstorm",
        96: "⚡ Thunderstorm with Hail",
        99: "⚡ Heavy Thunderstorm with Hail"
    }
    
    # Add additional weather codes that might be used by Open-Meteo
    if 100 <= weather_code <= 199:  # Various types of rain
        return "🌧️ Rain"
    elif 200 <= weather_code <= 299:  # Various types of thunderstorms
        return "⚡ Thunderstorm"
    elif 300 <= weather_code <= 399:  # Various types of drizzle
        return "🌧️ Drizzle"
    elif 400 <= weather_code <= 499:  # Various types of snow
        return "🌨️ Snow"
    elif 500 <= weather_code <= 599:  # Various types of fog
        return "🌫️ Fog"
    elif 600 <= weather_code <= 699:  # Various types of mist
        return "🌫️ Mist"
    elif 700 <= weather_code <= 799:  # Various types of dust
        return "💨 Dust"
    elif 800 <= weather_code <= 899:  # Various types of volcanic ash
        return "🌋 Ash"
    elif 900 <= weather_code <= 999:  # Various types of squalls
        return "🌪️ Squall"
    
    return weather_conditions.get(weather_code, "🌈 Unknown")

def get_water_recommendation(weather):
    """Get water recommendation based on weather conditions"""
    if weather.get('temp_max', 0) > 30 or weather.get('weather_code', 0) in [0, 1, 2]:
        return {
            'amount': 40,
            'frequency': 'daily'
        }
    elif weather.get('temp_max', 0) < 20 or weather.get('weather_code', 0) in [45, 48]:
        return {
            'amount': 20,
            'frequency': 'every 2 days'
        }
    else:
        return {
            'amount': 30,
            'frequency': 'every other day'
        }

def get_fertilizer_recommendation(weather):
    """Get fertilizer recommendation based on weather conditions"""
    if weather.get('temp_max', 0) > 30:
        return {
            'type': 'NPK 15-15-15',
            'amount': 200,
            'frequency': 'weekly'
        }
    elif weather.get('temp_max', 0) < 20:
        return {
            'type': 'NPK 10-10-10',
            'amount': 150,
            'frequency': 'bi-weekly'
        }
    else:
        return {
            'type': 'NPK 20-20-20',
            'amount': 180,
            'frequency': 'weekly'
        }

# Initialize components at the start
market_predictor = MarketPricePredictor()
market_predictor.set_data_path("data/market_prices.csv")

# Load city weather data
try:
    with open('data/city_weather_data.json', 'r', encoding='utf-8') as f:
        city_weather_data = json.load(f)
except FileNotFoundError:
    st.error("City weather data file not found!")
    city_weather_data = {}
except json.JSONDecodeError:
    st.error("Error loading city weather data!")
    city_weather_data = {}

# Load region-crop mapping
try:
    with open('data/region_crops.json', 'r', encoding='utf-8') as f:
        region_crops = json.load(f)
except FileNotFoundError:
    st.error("Region-crop mapping file not found!")
    region_crops = {}
except json.JSONDecodeError:
    st.error("Error loading region-crop mapping!")
    region_crops = {}

# Add custom CSS for sidebar background only
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background: linear-gradient(135deg, #f0f8ff 0%, #e8f5e9 100%) !important;
    border-right: 1px solid #d4edda !important;
    box-shadow: 2px 0 5px rgba(0,0,0,0.08) !important;
    min-width: 340px !important;
    max-width: 340px !important;
    width: 340px !important;
}

/* Ensure the sidebar form fields fit nicely */
section[data-testid="stSidebar"] .block-container {
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
}

/* Make greenhouse size input columns equal and full width */
section[data-testid="stSidebar"] .stColumns {
    display: flex;
    gap: 0.7rem !important;
}
section[data-testid="stSidebar"] .stColumn {
    flex: 1 1 0 !important;
}


/* Restore a natural gap between sidebar and main content */
div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
    margin-left: 38px !important;
}

/* Center weather info and set max width */
.weather-metrics-center {
    max-width: 900px;
    margin-left: auto;
    margin-right: auto;
}

/* Reasonable column widths for metrics */
div[data-testid="column"] {
    min-width: 170px !important;
    max-width: 240px !important;
}

/* Ensure metric values are fully visible and larger */
div[data-testid="stMetric"] > div > div:nth-child(2) {
    font-size: 2.1rem !important;
    white-space: nowrap !important;
    overflow: visible !important;
}

/* Add spacing below sidebar button */
section[data-testid="stSidebar"] button + div {
    margin-bottom: 2.5rem !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🌾 Crop-Planning Assistant – Weather Explorer")

# ─────────────────── Sidebar Input ───────────────────
import time

with st.sidebar:
    st.header("📍 Location")
    city: str = st.text_input("Type a Myanmar city / town name", placeholder="E.g. Yangon, Mandalay, Hpa-An …", key="city_input").strip()
    st.session_state['selected_city'] = city
    
    region = None
    for city_name, city_data in region_crops.items():
        if city.lower() == city_name.lower():
            region = city_data.get('region')
            break
    if not region:
        city_data = city_weather_data.get(city.lower(), {})
        region = city_data.get('region')
    st.session_state['selected_region'] = region

    st.header("📏 Greenhouse Size")
    col1, col2 = st.columns(2)
    with col1:
        length = st.number_input("Length (meters)", min_value=1.0, value=10.0, step=1.0, key="length")
    with col2:
        width = st.number_input("Width (meters)", min_value=1.0, value=5.0, step=1.0, key="width")

    if city and length and width:
        st.button("🔍 Get Weather & Crop Data", key="fetch_data")

    # Water and fertilizer info in sidebar (show after weather and market data)
    if st.session_state.get('weather_data_ready') and st.session_state.get('market_data_ready'):
        st.header("💧 Water & 🌱 Fertilizer Options")
        water_availability = st.number_input("Water availability (liters/day)", min_value=0, value=1000, key="water")
        fertilizer_type = st.selectbox("Select fertilizer type:", ["Organic", "Chemical", "Hybrid"], key="fertilizer")
        if 'water_recommendation' in st.session_state:
            water_recommendation = st.session_state['water_recommendation']
            st.info(f"Water: {water_recommendation['amount']} mm, {water_recommendation['frequency']}")
        if 'fertilizer_recommendation' in st.session_state:
            fertilizer_recommendation = st.session_state['fertilizer_recommendation']
            st.info(f"Fertilizer: {fertilizer_recommendation['type']} ({fertilizer_recommendation['amount']} kg/ha, {fertilizer_recommendation['frequency']})")
        # Reset flags so sidebar options do not persist after crop selection
        st.session_state['weather_data_ready'] = False
        st.session_state['market_data_ready'] = False

# Main content
if st.session_state.get('fetch_data'):
    try:
        # Store city in session state
        st.session_state['selected_city'] = city
        
        # Get region from city name
        region = st.session_state.get('selected_region')
        if not region:
            # Try to get region from city_weather_data first
            city_data = city_weather_data.get(city.lower(), {})
            region = city_data.get('region')
    except Exception as e:
        st.error(f"An error occurred: {e}")

    if not region:
        # If no region found in city_weather_data, try to map city to region
        city_region_mapping = {
                    # Central Plain Region
                    "mandalay": "central_plain",
                    "yangon": "central_plain",
                    "naypyidaw": "central_plain",
                    "bago": "central_plain",
                    "pyinmana": "central_plain",
                    "meiktila": "central_plain",
                    "thaungbya": "central_plain",
                    "magwe": "central_plain",
                    "minbu": "central_plain",
                    "pyay": "central_plain",
                    "sagaing": "central_plain",
                    "monywa": "central_plain",
                    "thaungtha": "central_plain",
                    "shwebo": "central_plain",
                    
                    # Coastal Region
                    "mawlamyine": "coastal",
                    "sittwe": "coastal",
                    "kyaukpyu": "coastal",
                    "pathein": "coastal",
                    "thaungzayat": "coastal",
                    "kyaikto": "coastal",
                    "ye": "coastal",
                    "mudon": "coastal",
                    "thandwe": "coastal",
                    "kyaukphyu": "coastal",
                    "ngapali": "coastal",
                    
                    # Hillside Region
                    "pyin oo lwin": "hillside",
                    "taunggyi": "hillside",
                    "myitkyina": "hillside",
                    "loikaw": "hillside",
                    "kengtung": "hillside",
                    "lashio": "hillside",
                    "kantaryaw": "hillside",
                    "kalay": "hillside",
                    "kale": "hillside",
                    "tamu": "hillside",
                    "kyaukme": "hillside",
                    "hpa-an": "hillside",
                    "kawkareik": "hillside",
                    "kyainseikgyi": "hillside"
                }
        region = city_region_mapping.get(city.lower(), None)

        if not region:
            st.error(f"Could not determine region for city: {city}. Please select a city from the list.")
            st.stop()

        # Store the region in session state
        st.session_state['selected_region'] = region

        # Get crops for the region
        crops = region_crops.get(region, {}).get('crops', [])
        if not crops:
            st.error(f"No crops found for region: {region}")
            st.stop()
        
        # Calculate area
        area = length * width
        
        # Convert city name to lowercase and replace spaces with underscores
        city_key = city.lower().replace(' ', '_')
        
        # Get weather data
        st.write("Fetching coordinates...")
        lat, lon = get_city_coordinates(city)
        if not lat or not lon:
            st.error(f"Could not find coordinates for city: {city}")
            st.stop()
            
        st.write(f"Coordinates found: Lat={lat}, Lon={lon}")
        st.write("Fetching weather data...")
        weather = get_open_meteo_weather(lat, lon)
        if not weather:
            st.error("No weather data received from API")
            st.stop()
        
        # Show weather metrics
        st.subheader("2. Weather Information")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌡️ Max Temperature", f"{weather.get('temp_max', 0):.1f}°C")
            st.metric("❄️ Min Temperature", f"{weather.get('temp_min', 0):.1f}°C")
            st.metric("💧 Humidity", f"{weather.get('humidity', 0):.1f}%")
            st.metric("🌍 Climate Zone", weather.get('climate_zone', 'N/A'))
            st.metric("💨 Wind Speed", f"{weather.get('wind_speed', 0):.1f}km/h")
            st.metric("🧭 Wind Direction", f"{weather.get('wind_direction', 0):.1f}°")
        with col2:
            st.metric("🌱 Soil Temperature", f"{weather.get('soil_temperature', 0):.1f}°C")
            st.metric("💧 Soil Moisture", f"{weather.get('soil_moisture', 0):.1f}%")
        with col3:
            st.metric("🌧️ Precipitation", f"{weather.get('precipitation', 0):.1f}mm")
            st.metric("💦 Evaporation Rate", f"{weather.get('evaporation_rate', 0):.1f}mm/day")
            weather_code = weather.get('weather_code', 0)
            weather_condition = get_weather_condition(weather_code)
            if weather_condition and ' ' in weather_condition:
                emoji, description = weather_condition.split(' ', 1)
            else:
                emoji, description = '', weather_condition
            st.metric(f"{emoji} Weather", description)
            st.metric(label="🌅 Sunrise", value=weather.get('sunrise', 'N/A')[-8:])
            st.metric(label="🌇 Sunset", value=weather.get('sunset', 'N/A')[-8:])
        
        # Show market price data for top 5 crops
        show_market_prices("Export Prices.csv", num_crops=5)

        # --- Show water/fertilizer in sidebar after successful weather fetch ---
        weather_for_recommend = weather if weather else {'temperature': 28, 'weather_code': 1}
        st.session_state['water_recommendation'] = get_water_recommendation(weather_for_recommend)
        st.session_state['fertilizer_recommendation'] = get_fertilizer_recommendation(weather_for_recommend)
        st.session_state['weather_data_ready'] = True
        st.session_state['market_data_ready'] = True

        # Delay before showing water/fertilizer info
        if not st.session_state.get('show_water_fertilizer'):
            time.sleep(3)
            st.session_state['show_water_fertilizer'] = True

        # Display water and fertilizer information
        st.write("\n")
        st.subheader("4. Water and Fertilizer Information")
        
        # Get water and fertilizer recommendations
        water_recommendation = get_water_recommendation(weather)
        fertilizer_recommendation = get_fertilizer_recommendation(weather)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="💧 Water Recommendation",
                value=f"{water_recommendation['amount']} mm",
                delta=f"{water_recommendation['frequency']}"
            )
        with col2:
            st.metric(
                label="🌱 Fertilizer Recommendation",
                value=fertilizer_recommendation['type'],
                delta=f"{fertilizer_recommendation['amount']} kg/ha"
            )
        
        # Add water and fertilizer details
        st.write("\n")
        st.subheader("Water and Fertilizer Details")
        st.write(f"Water amount: {water_recommendation['amount']} mm")
        st.write(f"Water frequency: {water_recommendation['frequency']}")
        st.write(f"Fertilizer type: {fertilizer_recommendation['type']}")
        st.write(f"Fertilizer amount: {fertilizer_recommendation['amount']} kg/ha")
        st.write(f"Fertilizer frequency: {fertilizer_recommendation['frequency']}")
        
# If no city or greenhouse size provided
if not city or not length or not width:
    st.warning("Please provide a city and greenhouse size to continue.")
    st.stop()

