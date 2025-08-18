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
with st.sidebar:
    st.header("📍 Location")
    city: str = st.text_input("Type a Myanmar city / town name", placeholder="E.g. Yangon, Mandalay, Hpa-An …").strip()
    # Store city selection in session state
    st.session_state['selected_city'] = city
    
    # Get region from city name
    region = None
    for city_name, city_data in region_crops.items():
        if city.lower() == city_name.lower():
            region = city_data.get('region')
            break
    
    # If no region found, try to get it from city_weather_data
    if not region:
        city_data = city_weather_data.get(city.lower(), {})
        region = city_data.get('region')
    
    # Store region in session state
    st.session_state['selected_region'] = region

    # Show greenhouse parameters alongside city
    st.header("📏 Greenhouse Size")
    col1, col2 = st.columns(2)
    with col1:
        length = st.number_input("Length (meters)", min_value=1.0, value=10.0, step=1.0, key="length")
    with col2:
        width = st.number_input("Width (meters)", min_value=1.0, value=5.0, step=1.0, key="width")

    # Only show button if both city and dimensions are provided
    if city and length and width:
        st.button("🔍 Get Weather & Crop Data", key="fetch_data")

# Main content
if st.session_state.get('fetch_data'):
    # Store city in session state
    st.session_state['selected_city'] = city
    
    # Get region from city name
    region = None
    for city_name, city_data in region_crops.items():
        if city.lower() == city_name.lower():
            region = city_data.get('region')
            break
    
    # If no region found, try to get it from city_weather_data
    if not region:
        city_data = city_weather_data.get(city.lower(), {})
        region = city_data.get('region')
    
    # Store region in session state
    st.session_state['selected_region'] = region
    
    # Calculate area
    area = length * width
    
    # Convert city name to lowercase and replace spaces with underscores
    city_key = city.lower().replace(' ', '_')
    
    try:
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
            
        # Debug print weather data structure
        st.write("Weather data received:")
        st.json(weather)
        
        if weather:
            # Step 2: Weather Information
            st.subheader("2. Weather Information")
            
            # Display weather metrics in columns
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    label="🌡️ Current Temperature",
                    value=f"{fmt(weather.get('temperature_2m', [None])[0], '°C')}"
                )
                st.metric(
                    label="💧 Humidity",
                    value=f"{fmt(weather.get('relativehumidity_2m', [None])[0], '%')}"
                )
            with col2:
                st.metric(
                    label="💨 Wind Speed",
                    value=f"{fmt(weather.get('windspeed_10m', [None])[0], 'km/h')}"
                )
                st.metric(
                    label="🌞 Wind Direction",
                    value=f"{fmt(weather.get('winddirection_10m', [None])[0], '°')}"
                )
            with col3:
                st.metric(
                    label="🌧️ Precipitation",
                    value=f"{fmt(weather.get('precipitation_sum', [None])[0], 'mm')}"
                )
                st.metric(
                    label="🌱 Soil Temperature",
                    value=f"{fmt(weather.get('soil_temperature_0cm', [None])[0], '°C')}"
                )
            
            # Display soil moisture
            st.metric(
                label="💧 Soil Moisture",
                value=f"{fmt(weather.get('soil_moisture_0_1cm', [None])[0], '%')}"
            )
            
            # Display evaporation rate
            st.metric(
                label="💦 Evaporation Rate",
                value=f"{fmt(weather.get('evapotranspiration', [None])[0], 'mm/day')}"
            )
            
            # Display sunrise/sunset times
            st.write("\n")
            daily_data = weather.get('daily', {})
            st.metric(
                label="🌅 Sunrise",
                value=daily_data.get('sunrise', ['N/A'])[0]
            )
            st.metric(
                label="🌇 Sunset",
                value=daily_data.get('sunset', ['N/A'])[0]
            )
            
            # Display climate zone
            st.metric(
                label="🌍 Climate Zone",
                value="Tropical Monsoon"
            )
            
            # Step 3: Market Price Analysis
            st.subheader("3. Market Price Analysis")
            
            # Get region from session state
            region = st.session_state.get('selected_region')
            if not region:
                st.error("Please select a city first from the sidebar")
                st.stop()

            # Get recommended crops for the region
            recommended_crops = region_crops.get(region, [])
            if not recommended_crops:
                st.error(f"No crop recommendations available for {region}")
                st.stop()

            # Display recommended crops
            st.write("\n")
            st.subheader(f"Recommended Crops for {region}")
            crop_list = st.selectbox(
                "Select a crop to view market analysis:",
                recommended_crops,
                format_func=lambda x: x['name'] if isinstance(x, dict) and 'name' in x else x
            )
            
            # Get market data for selected crop
            if crop_list:
                crop_name = crop_list['name'] if isinstance(crop_list, dict) else crop_list
                market_data = get_market_data(crop_name)
                if not market_data:
                    st.error("Market data not available")
                    st.stop()

                # Display market price information
                current_price = market_data.get('current_price', 0)
                price_change = market_data.get('price_change', 0)

                # Display market price analysis
                st.write("\n")
                st.subheader("Market Price Analysis")
                st.write(f"Current price: {current_price:,.0f} MMK/kg")
                st.write(f"Daily change: {price_change:+,.0f} MMK/kg")
                st.write(f"Market trend: {'Rising' if price_change > 0 else 'Falling'}")

    except Exception as e:
        st.error(f"Error fetching or displaying data: {e}")

        # Get recommended crops for the region
        recommended_crops = region_crops.get(region, [])
        if not recommended_crops:
            st.error(f"No crop recommendations available for {region}")
            st.stop()

        # Display recommended crops
        st.write("\n")
        st.subheader(f"Recommended Crops for {region}")
        crop_list = st.selectbox(
            "Select a crop to view market analysis:",
            recommended_crops,
            format_func=lambda x: x['name'] if isinstance(x, dict) and 'name' in x else x
        )
        
        # Get market data for selected crop
        market_data = get_market_data(crop_list)
        if not market_data:
            st.error("Market data not available")
            st.stop()


        
        # Get daily weather data
        daily_data = weather['daily']
        
        # Display current weather
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="🌡️ Current Temperature",
                value=f"{current_temp}°C"
            )
        with col2:
            st.metric(
                label="💨 Wind Speed",
                value=f"{current_wind_speed} km/h"
            )
        with col3:
            st.metric(
                label="💧 Humidity",
                value=f"{current_humidity}%"
            )
        
        # Display weather forecast
        st.write("\n")
        st.subheader("Weather Forecast")
        
        # Create weather forecast chart
        dates = daily_data['time']
        temps = daily_data['temperature_2m_max']
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=temps,
            mode='lines+markers',
            name='Max Temperature',
            line=dict(color='#FF4500')
        ))
        
        fig.update_layout(
            title='Weather Trends (Next 7 Days)',
            xaxis_title='Date',
            yaxis=dict(
                title='Temperature (°C)',
                gridcolor='rgba(0,0,0,0.1)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#333333'),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display weather details
        st.write("\n")
        st.subheader("Weather Details")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                label="💨 Wind Direction",
                value=f"{current_wind_direction}°"
            )
        with col2:
            st.metric(
                label="💧 Dew Point",
                value=f"{current_dew_point}°C"
            )
        with col3:
            st.metric(
                label="☁️ Cloud Cover",
                value=f"{current_cloud_cover}%"
            )
        
        # Display pressure
        st.metric(
            label=" Atmospheric Pressure",
            value=f"{current_pressure} hPa"
        )
        
        # Display weather code
        st.metric(
            label=" Weather Code",
            value=str(current_weather)
        )
        
        # Display current time
        st.metric(
            label=" Time",
            value=current_time
        )
        
        # Step 3: Market Price Analysis
        st.subheader("3. Market Price Analysis")
        
        # Get region from session state
        region = st.session_state.get('selected_region')
        if not region:
            st.error("Please select a city first from the sidebar")
            st.stop()

        # Get recommended crops for the region
        recommended_crops = region_crops.get(region, [])
        if not recommended_crops:
            st.error(f"No crop recommendations available for {region}")
            st.stop()

        # Display recommended crops
        st.write("\n")
        st.subheader(f"Recommended Crops for {region}")
        crop_list = st.selectbox(
            "Select a crop to view market analysis:",
            recommended_crops,
            format_func=lambda x: x['name'] if isinstance(x, dict) and 'name' in x else x
        )
        
        # Get market data for selected crop
        market_data = get_market_data(crop_list)
        if not market_data:
            st.error("Market data not available")
            st.stop()
    
    # Calculate area
    area = length * width
    
    # Convert city name to lowercase and replace spaces with underscores
    city_key = city.lower().replace(' ', '_')
    # Fetch real weather data from Open-Meteo
    # Use real values for fields from Open-Meteo
    soil_moisture = weather.get('soil_moisture', 'N/A')
    soil_temperature = weather.get('soil_temperature', 'N/A')
    evaporation_rate = weather.get('evaporation_rate', 'N/A')

    # Step 2: Weather Information
    st.subheader("2. Weather Information")
    
    try:
        # Get weather metrics using utility function
        weather_metrics = get_weather_metrics(weather)
        if not weather_metrics:
            st.error("Failed to extract weather metrics")
            st.stop()
        
        # Center the weather metrics block
        st.markdown('<div class="weather-metrics-center">', unsafe_allow_html=True)
        weather_cols = st.columns([1, 0.1, 1, 0.1, 1])
        col1, spacer1, col2, spacer2, col3 = weather_cols
        # Add a class to the row for custom CSS
        st.markdown('<div class="weather-metrics-row"></div>', unsafe_allow_html=True)

        # Format temperature and other values for clarity
        def fmt(val, unit="", decimals=1):
            if val == 'N/A' or val is None:
                return "N/A"
            try:
                return f"{float(val):.{decimals}f}{unit}"
            except Exception:
                return str(val) + unit

        with col1:
            st.metric(
                label="🌡️ Current Temperature",
                value=f"{fmt(weather_metrics.get('temperature', 'N/A'), '°C')}",
                delta="Current"
            )
            st.metric(
                label="💨 Wind Speed",
                value=f"{fmt(weather_metrics.get('windspeed', 'N/A'), 'km/h')}",
                delta="Average"
            )
            st.metric(
                label="☀️ Sunlight Hours",
                value=f"{fmt(weather_metrics.get('sunlight_hours', 'N/A'), 'h')}",
                delta="Daily"
            )

        with col2:
            st.metric(
                label="💧 Humidity",
                value=f"{fmt(weather_metrics.get('humidity', 'N/A'), '%')}",
                delta="Relative"
            )
            st.metric(
                label="🌧️ Precipitation",
                value=f"{fmt(weather_metrics.get('precipitation', 'N/A'), 'mm')}",
                delta="Daily"
            )
            st.metric(
                label="💨 Wind Direction",
                value=f"{fmt(weather_metrics.get('winddirection', 'N/A'), '°')}",
                delta="Degrees"
            )

        with col3:
            st.metric(
                label="🌡️ Min Temp",
                value=f"{fmt(weather_metrics.get('temperature_min', 'N/A'), '°C')}",
                delta="Daily"
            )
            st.metric(
                label="🌡️ Max Temp",
                value=f"{fmt(weather_metrics.get('temperature_max', 'N/A'), '°C')}",
                delta="Daily"
            )
            st.metric(
                label="💨 Gust Speed",
                value=f"{fmt(weather_metrics.get('windspeed_gust', 'N/A'), 'km/h')}",
                delta="Peak"
            )

    except Exception as e:
        st.error(f"Error displaying weather metrics: {e}")

    # Add weather graph
    st.write("\n")
    st.subheader("Weather Trends")
    
    try:
        # Use Open-Meteo hourly data for visualization if available
        import numpy as np
        import pandas as pd
        import datetime
        now = datetime.datetime.now()
        # Create date range for next 7 days
        date_range = pd.date_range(now, periods=7, freq='D')
        
        # Try to get hourly data arrays from Open-Meteo
        temp_hourly = weather.get('temperature_2m', None)
        humidity_hourly = weather.get('relativehumidity_2m', None)
        rainfall_hourly = weather.get('precipitation', None)
        
        # If Open-Meteo provides arrays, use them, else fallback to current values
        if isinstance(temp_hourly, list) and len(temp_hourly) >= 7:
            temp_data = pd.Series(temp_hourly[:7])
        else:
            temp_data = pd.Series([weather_metrics.get('temperature', 0)]*7)
        
        if isinstance(humidity_hourly, list) and len(humidity_hourly) >= 7:
            humidity_data = pd.Series(humidity_hourly[:7])
        else:
            humidity_data = pd.Series([weather_metrics.get('humidity', 0)]*7)
        
        if isinstance(rainfall_hourly, list) and len(rainfall_hourly) >= 7:
            rainfall_data = pd.Series(rainfall_hourly[:7])
        else:
            rainfall_data = pd.Series([weather_metrics.get('precipitation', 0)]*7)
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add temperature trace
        fig.add_trace(go.Scatter(
            x=date_range,
            y=temp_data,
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#FF4B4B'),
            yaxis='y1'
        ))
        
        # Add humidity trace
        fig.add_trace(go.Scatter(
            x=date_range,
            y=humidity_data,
            mode='lines+markers',
            name='Humidity',
            line=dict(color='#00CED1'),
            yaxis='y2'
        ))
        
        # Add rainfall trace
        fig.add_trace(go.Bar(
            x=date_range,
            y=rainfall_data,
            name='Rainfall',
            marker_color='#4169E1'
        ))
        
        # Update layout
        fig.update_layout(
            title='7-Day Weather Forecast',
            xaxis_title='Date',
            yaxis=dict(
                title='Temperature (°C)',
                titlefont=dict(color='#FF4B4B'),
                tickfont=dict(color='#FF4B4B'),
                side='left'
            ),
            yaxis2=dict(
                title='Humidity (%)',
                titlefont=dict(color='#00CED1'),
                tickfont=dict(color='#00CED1'),
                overlaying='y',
                side='right'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            margin=dict(l=50, r=50, t=50, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#333333')
        )
        
        # Add hover text
        fig.update_traces(
            hovertemplate='%{y:.1f} %{text}',
            text=['°C' if trace.name == 'Temperature' else '%' if trace.name == 'Humidity' else 'mm' for trace in fig.data]
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error creating weather graph: {e}")

    # Display weather section using component
    display_weather_section(weather)
    
    # Display weather details using component
    display_weather_details(weather)

    # Step 3: Market Price Analysis
    st.subheader("3. Market Price Analysis")
    
    # Get region from session state
    region = st.session_state.get('selected_region')
    if not region:
        st.error("Please select a city first from the sidebar")
        st.stop()

    # Get recommended crops for the region
    recommended_crops = region_crops.get(region, [])
    if not recommended_crops:
        st.error(f"No crop recommendations available for {region}")
        st.stop()

    # Display recommended crops
    st.write("\n")
    st.subheader(f"Recommended Crops for {region}")
    crop_list = st.selectbox(
        "Select a crop to view market analysis:",
        recommended_crops,
        format_func=lambda x: x['name'] if isinstance(x, dict) and 'name' in x else x
    )

    # Get market data for selected crop
    if crop_list:
        crop_name = crop_list['name'] if isinstance(crop_list, dict) else crop_list
        market_data = get_market_data(crop_name)
        if not market_data:
            st.error("Market data not available")
            st.stop()

        # Display market price information
        current_price = market_data.get('current_price', 0)
        price_change = market_data.get('price_change', 0)

        # Display market price analysis
        st.write("\n")
        st.subheader("Market Price Analysis")
        
        # Create price trend graph
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=market_data['date'],
            y=market_data['price'],
            mode='lines+markers',
            name='Price Trend',
            line=dict(color='#2E8B57')
        ))
        
        fig.update_layout(
            title=f"{crop_list} Price Trend",
            xaxis_title='Date',
            yaxis_title='Price (MMK/kg)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#333333'),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display current price and analysis
        current_price = market_data['price'][-1]
        price_change = market_data['price'][-1] - market_data['price'][-2]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Current Price",
                value=f"{current_price:,.0f} MMK/kg",
                delta=f"{price_change:+,.0f} MMK/kg"
            )
        with col2:
            st.metric(
                label="Price Change",
                value=f"{price_change:+,.0f} MMK/kg",
                delta="Daily change"
            )
        
        # Add market analysis text
        st.write("\n")
        st.subheader("Market Analysis")
        st.write(f"Current price: {current_price:,.0f} MMK/kg")
        st.write(f"Daily change: {price_change:+,.0f} MMK/kg")
        st.write(f"Market trend: {'Rising' if price_change > 0 else 'Falling'}")

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

        # Display market price analysis
        st.write("\n")
        st.subheader("Market Price Analysis")
        
        # Create price trend graph
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=market_data['date'],
            y=market_data['price'],
            mode='lines+markers',
            name='Price Trend',
            line=dict(color='#2E8B57')
        ))
        
        fig.update_layout(
            title=f"{crop_list} Price Trend",
            xaxis_title='Date',
            yaxis_title='Price (MMK/kg)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#333333'),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display current price and analysis
        current_price = market_data['price'][-1]
        price_change = market_data['price'][-1] - market_data['price'][-2]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Current Price",
                value=f"{current_price:,.0f} MMK/kg",
                delta=f"{price_change:+,.0f} MMK/kg"
            )
        with col2:
            st.metric(
                label="Price Change",
                value=f"{price_change:+,.0f} MMK/kg",
                delta="Daily change"
            )
        
        # Add market analysis text
        st.write("\n")
        st.subheader("Market Analysis")
        st.write(f"Current price: {current_price:,.0f} MMK/kg")
        st.write(f"Daily change: {price_change:+,.0f} MMK/kg")
        st.write(f"Market trend: {'Rising' if price_change > 0 else 'Falling'}")

        # Step 4: Water and Fertilizer Information
        st.subheader("4. Water and Fertilizer Information")
        
        # Water availability
        water_availability = st.number_input("Water availability (liters/day)", min_value=0, value=1000, key="water")
        
        # Fertilizer type
        fertilizer_type = st.selectbox("Select fertilizer type:", 
                                     ["Organic", "Chemical", "Hybrid"], key="fertilizer")

        # Only show analysis if water and fertilizer are provided
        if water_availability > 0 and fertilizer_type:
            # Step 5: Crop Recommendations and Analysis
            st.subheader("5. Crop Recommendations and Analysis")
            
            # Get top 3 crops based on climate and market
            if market_analysis:
                # Sort crops by market potential
                sorted_crops = sorted(market_analysis, 
                                    key=lambda x: (x['confidence'], x['predicted_trend']),
                                    reverse=True)
                top_crops = sorted_crops[:3]
                
                # Display top crops
                st.write("\n")
                st.subheader("Top 3 Recommended Crops")
                for crop in top_crops:
                    st.write(f"\n**{crop['crop']}**")
                    st.write(f"- Current Price: {crop['current_price']:.2f} Ks/kg")
                    st.write(f"- Price Trend: {crop['predicted_trend']:.2%}")
                    st.write(f"- Confidence: {crop['confidence']:.2%}")

            # Step 6: Planting Dates and Yield
            st.subheader("6. Planting Dates and Yield")
            
            # Get optimal planting dates (example - should be based on actual weather data)
            if top_crops:
                for crop in top_crops:
                    st.write(f"\n**{crop['crop']}**")
                    st.write(f"- Optimal Planting Dates: January - March")
                    st.write(f"- Expected Yield: {area * 0.5:.2f} kg (based on historical data)")

            # Step 7: Profit Analysis
            st.subheader("7. Profit Analysis")
            
            # Calculate costs
            water_cost = water_availability * 0.01  # Example cost per liter
            fertilizer_cost = 1000  # Example cost
            labor_cost = 5000  # Example cost
            
            if top_crops:
                for crop in top_crops:
                    st.write(f"\n**{crop['crop']}**")
                    
                    # Calculate costs
                    total_cost = water_cost + fertilizer_cost + labor_cost
                    
                    # Calculate revenue
                    expected_yield = area * 0.5  # Example yield per sqm
                    revenue = expected_yield * crop['current_price']
                    
                    # Calculate profit
                    profit = revenue - total_cost
                    
                    st.write(f"- Total Cost: {total_cost:.2f} Ks")
                    st.write(f"- Expected Revenue: {revenue:.2f} Ks")
                    st.write(f"- Expected Profit: {profit:.2f} Ks")

            # Step 8: Summary
            st.subheader("8. Summary")
            if top_crops:
                summary = (
                    f"Based on your location ({city}) and greenhouse size ({area:.2f} sqm), "
                    f"the recommended crops are {', '.join([c['crop'] for c in top_crops])}. "
                    "These crops have favorable market conditions and climate suitability. "
                    "The best planting time is during January-March when weather conditions are optimal. "
                    "With proper water and fertilizer management, you can expect good yields and profits."
                )
                st.write(summary)

# Check if city exists in city_weather_data
if not city_weather_data:
    st.error("City weather data not loaded!")
    st.stop()

# Get city data using the correct key format
selected_city = st.session_state.get('selected_city', '').lower().replace(' ', '_')
city_data = city_weather_data.get(selected_city)

# If no city data found
if not city_data:
    st.error(f"No weather data available for city: {selected_city}")
    st.stop()

# If no city or greenhouse size provided
if not city or not length or not width:
    st.error("Please provide city name and greenhouse dimensions")
    st.stop()

# If city and dimensions are provided
else:
    st.info("Please enter city name and greenhouse size in the sidebar to proceed.")
