import os
import sys
import json
import time
import os
import sys
import json
import time
import numpy as np
import pandas as pd
import streamlit as st
import base64
import plotly.graph_objects as go
import math
import re
from typing import Dict, Any, List
from datetime import datetime, timedelta

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import our project modules
from app.ui_helpers import load_css, show_home_page
from app.dashboard_sections import display_weather_information, display_forecast_graph, display_main_market_data, display_ml_recommendations, display_cost_and_roi
from app.ml_crop_recommender import recommend_crops # The new recommendation engine
from app.profit_predictor import predict_profit  # Import the profit predictor
from src.data_collection.weather import get_open_meteo_weather as get_weather_data

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import our project modules
from app.ui_helpers import load_css, show_home_page
from app.dashboard_sections import display_weather_information, display_forecast_graph, display_main_market_data, display_ml_recommendations
from app.ml_crop_recommender import recommend_crops # The new recommendation engine
from src.data_collection.weather import get_open_meteo_weather as get_weather_data

# --- Default values and constants ---
DEFAULT_GREENHOUSE_SIZE = 100.0
CITY_COORDINATES = {
    "Pathein (Ayeyarwady)": {"lat": 16.78, "lon": 94.73}, "Bago": {"lat": 17.34, "lon": 96.48},
    "Hakha (Chin)": {"lat": 22.64, "lon": 93.61}, "Loikaw (Kayah)": {"lat": 19.67, "lon": 97.21},
    "Hpa-an (Kayin)": {"lat": 16.89, "lon": 97.63}, "Magway": {"lat": 20.15, "lon": 94.95},
    "Mandalay": {"lat": 21.96, "lon": 96.09}, "Mawlamyine (Mon)": {"lat": 16.49, "lon": 97.63},
    "Naypyidaw": {"lat": 19.76, "lon": 96.08}, "Sittwe (Rakhine)": {"lat": 20.14, "lon": 92.90},
    "Sagaing": {"lat": 21.88, "lon": 95.98}, "Taunggyi (Shan)": {"lat": 20.78, "lon": 97.03},
    "Dawei (Tanintharyi)": {"lat": 14.08, "lon": 98.20}, "Yangon": {"lat": 16.87, "lon": 96.19}
}

# Load external CSS
load_css("assets/styles/dashboard.css")

# --- Load crop names for preferred crop dropdown (define once) ---
if "CROP_OPTIONS" not in globals():
    CROP_OPTIONS: list[str] = []
    try:
        crop_json_path = os.path.join(PROJECT_ROOT, "data", "crop_settings.json")
        if os.path.isfile(crop_json_path):
            with open(crop_json_path, "r", encoding="utf-8") as f:
                _crop_data_all = json.load(f)
            CROP_OPTIONS = sorted({entry["crop_name"] for crops in _crop_data_all.values() for entry in crops})
    except Exception:
        CROP_OPTIONS = []

# --- Page Routing ---
if 'show_dashboard' not in st.session_state:
    st.session_state['show_dashboard'] = False

if not st.session_state.get('show_dashboard', False):
    show_home_page()
    st.stop()

# --- Main Dashboard UI ---
if st.session_state.get('show_dashboard'):
    st.title("🌿 GreenThumb AI: Crop Strategy Assistant")

    with st.sidebar:
        st.header("📍 Location")
        township_options = [
            "Select a location...", "Pathein (Ayeyarwady)", "Bago", "Hakha (Chin)", "Loikaw (Kayah)", 
            "Hpa-an (Kayin)", "Magway", "Mandalay", "Mawlamyine (Mon)", "Naypyidaw",
            "Sittwe (Rakhine)", "Sagaing", "Taunggyi (Shan)", "Dawei (Tanintharyi)", "Yangon"
        ]
        city_full: str = st.selectbox("Select your city / township", township_options, key="city_input")
        city = city_full.split(" (")[0] if city_full != "Select a location..." else ""

        # --- THIS SECTION IS RESTORED TO ITS ORIGINAL FUNCTIONALITY ---
        st.header("📏 Greenhouse Size")
        area_input = ""
        def check_for_custom_selection():
            if st.session_state.greenhouse_size_selector == "Custom...":
                st.session_state.custom_mode = True
        def return_to_select_mode():
            st.session_state.custom_mode = False
            st.session_state.greenhouse_size_selector = "Select a size..."
        size_widget_placeholder = st.empty()
        if st.session_state.get("custom_mode", False):
            area_input = size_widget_placeholder.text_input("Enter custom area (sq. meters)", key="custom_area_input", placeholder="e.g., 130")
            st.button("↩️ Back to list", on_click=return_to_select_mode, key="size_back_button")
        else:
            size_options = ["Select a size...", "50", "100", "150", "200", "300", "500", "Custom..."]
            selected_size = size_widget_placeholder.selectbox("Greenhouse size (sq. meters)", size_options, key="greenhouse_size_selector", on_change=check_for_custom_selection)
            if selected_size and selected_size not in ["Select a size...", "Custom..."]:
                area_input = selected_size
        
        with st.expander("⚙️ Advanced settings", expanded=False):
            st.header("🚰 Water & Fertilizer")
            water_availability = ""
            def check_for_water_custom_selection():
                if st.session_state.water_availability_selector == "Custom...":
                    st.session_state.water_custom_mode = True
            def return_to_water_select_mode():
                st.session_state.water_custom_mode = False
                st.session_state.water_availability_selector = "Select amount..."
            water_widget_placeholder = st.empty()
            if st.session_state.get("water_custom_mode", False):
                water_availability = water_widget_placeholder.text_input("Enter water availability (liters per day)", key="custom_water_input", placeholder="e.g., 1500")
                st.button("↩️ Back", on_click=return_to_water_select_mode, key="water_back_button")
            else:
                water_options = ["Select amount...", "100", "300", "500", "700", "1000", "1500", "Custom..."]
                selected_water = water_widget_placeholder.selectbox("Water availability (liters per day)", water_options, key="water_availability_selector", on_change=check_for_water_custom_selection)
                if selected_water and selected_water not in ["Select amount...", "Custom..."]:
                    water_availability = selected_water

            fertilizer_type = st.selectbox("Fertilizer type", ["Organic", "Chemical", "Hybrid"], key="fertilizer_type")

            # Preferred crop selection
            if CROP_OPTIONS:
                pref_options = ["No preference"] + CROP_OPTIONS
                st.selectbox("Preferred crop (optional)", pref_options, key="preferred_crop")
        # --- END ADVANCED SETTINGS ---

        # Dark mode toggle
        st.markdown("---")
        st.checkbox("🌙 Dark mode", key="dark_mode_toggle")
        st.session_state['dark_mode'] = st.session_state.get('dark_mode_toggle', False)

        # Apply dark mode theme immediately when toggled
        if st.session_state['dark_mode']:
            load_css("assets/styles/dashboard_dark.css")
            st.markdown(
                """
                <script>
                const docBody = window.parent.document.body;
                if (docBody) { docBody.classList.add('dark-mode'); }
                </script>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <script>
                const docBody = window.parent.document.body;
                if (docBody) { docBody.classList.remove('dark-mode'); }
                </script>
                """,
                unsafe_allow_html=True,
            )

        def set_fetch_data():
            st.session_state["fetch_data"] = True

        if city and area_input and water_availability:
            st.button("🔍 Get Recommendations", key="fetch_data_btn", on_click=set_fetch_data)

# --- Data Fetching and Processing Block ---
if st.session_state.get("fetch_data", False):
    with st.spinner("🛰️ Fetching weather and analyzing your inputs..."):
        # The values from the widgets are already in st.session_state.
        # We only need to validate the numeric inputs and store them.
        try:
            st.session_state['area_sqm'] = float(area_input)
            st.session_state['water_liters'] = float(water_availability)
        except (ValueError, TypeError):
            st.error("Please enter valid numbers for greenhouse area and water availability.")
            st.session_state['fetch_data'] = False
            st.stop()

        location_info = CITY_COORDINATES.get(city_full)
        if not location_info:
            st.error(f"Could not find location information for '{city_full}'.")
            st.session_state['fetch_data'] = False
            st.stop()
        
        weather = get_weather_data(location_info['lat'], location_info['lon'])
        if not weather:
            st.error("💨 No weather data received. Please try again later.")
            st.session_state['fetch_data'] = False
            st.stop()
            
        st.session_state['weather_data'] = weather
        st.session_state['data_ready'] = True
        st.session_state['fetch_data'] = False

# --- Main Content Display Block ---
if st.session_state.get("data_ready", False):
    weather = st.session_state.get('weather_data', {})
    # --- MODIFIED: Retrieve using the widget's key ---
    city_full = st.session_state.get('city_input', '')
    area_sqm = st.session_state.get('area_sqm', DEFAULT_GREENHOUSE_SIZE)
    water_liters = st.session_state.get('water_liters', 0.0)
    # --- MODIFIED: Retrieve using the widget's key ---
    fert_type = st.session_state.get('fertilizer_type', 'Organic')

    st.markdown(f"📍 **Displaying results for:** `{city_full}` | **Greenhouse Area:** `{area_sqm} sqm`")
    
    display_weather_information(st, weather)
    display_forecast_graph(st, weather, go)
    display_main_market_data(st)

    st.markdown("## 🌿 AI Crop Recommendations & Planning")
    with st.spinner("🧠 Analyzing your farm data for top crop choices..."):
        
        # Cache the recommendation engine to speed up repeats with same inputs
        @st.cache_data(show_spinner=False)
        def get_recommendations_cached(city, area, water, fert, weather):
            return recommend_crops(
                city=city,
                greenhouse_size=area,
                water_availability=water,
                fertilizer_type=fert,
                weather_data=weather,
            )

        recommendations = get_recommendations_cached(
            city_full,
            area_sqm,
            water_liters,
            fert_type,
            weather,
        )

        if not recommendations:
            st.info("No suitable crop recommendations found. Try adjusting the inputs.")
            st.stop()

        # Handle preferred crop logic
        preferred_crop = st.session_state.get("preferred_crop", "No preference")

        if preferred_crop and preferred_crop != "No preference":
            matching = [rec for rec in recommendations if rec["crop_name"].lower() == preferred_crop.lower()]
            if matching:
                st.markdown(f"### 🌟 Preferred Crop Match: **{preferred_crop}**")
                display_ml_recommendations(
                    st_obj=st,
                    recommendations=matching,
                    area_input=str(area_sqm)
                )
            else:
                st.markdown(
                    f"""
                    <div style='padding:16px; background-color:#FFF4E5; border-left:4px solid #FFA726; border-radius:6px; margin-bottom:16px;'>
                        <strong>⚠️ Preferred crop "{preferred_crop}" is not suitable under the current conditions.</strong><br/>
                        Here are the best-suited crops instead:
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                display_ml_recommendations(
                    st_obj=st,
                    recommendations=recommendations,
                    area_input=str(area_sqm)
                )
        else:
            display_ml_recommendations(
                st_obj=st,
                recommendations=recommendations,
                area_input=str(area_sqm)
            )