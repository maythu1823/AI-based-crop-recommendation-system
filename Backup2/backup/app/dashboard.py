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
from utils.weather_utils import calculate_sunlight_hours

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
    try:
        # Store city in session state
        st.session_state['selected_city'] = city
        
        # Get region from city name
        region = st.session_state.get('selected_region')
        if not region:
            # Try to get region from city_weather_data first
            city_data = city_weather_data.get(city.lower(), {})
            region = city_data.get('region')
            
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
            
        # Debug print weather data structure
        if weather:
            # Step 2: Weather Information
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
                # Show current weather condition as a metric
                weather_code = weather.get('weather_code', 0)
                weather_condition = get_weather_condition(weather_code)
                # Extract emoji and description
                if weather_condition and ' ' in weather_condition:
                    emoji, description = weather_condition.split(' ', 1)
                else:
                    emoji, description = '', weather_condition
                st.metric(f"{emoji} Weather", description)

            with col3:
                st.metric(
                    label="💨 Wind Speed",
                    value=f"{fmt(weather.get('wind_speed', 'N/A'), 'km/h')}"
                )
                st.metric(
                    label="🧭 Wind Direction",
                    value=f"{fmt(weather.get('wind_direction', 'N/A'), '°')}"
                )
                st.metric(
                    label="🌅 Sunrise",
                    value=weather.get('sunrise', 'N/A')[-8:]
                )
                st.metric(
                    label="🌇 Sunset",
                    value=weather.get('sunset', 'N/A')[-8:]
                )

        # Weather Trends section (moved above market price data)
        st.subheader("Weather Trends")
        try:
            import numpy as np
            import pandas as pd
            import datetime
            now = datetime.datetime.now()
            date_range = pd.date_range(now, periods=7, freq='D')
            temp_hourly = weather.get('temperature_2m', None)
            humidity_hourly = weather.get('relativehumidity_2m', None)
            rainfall_hourly = weather.get('precipitation', None)
            if isinstance(temp_hourly, list) and len(temp_hourly) >= 7:
                temp_data = pd.Series(temp_hourly[:7])
            else:
                temp_data = pd.Series([weather.get('temp_max', 0)]*7)
            if isinstance(humidity_hourly, list) and len(humidity_hourly) >= 7:
                humidity_data = pd.Series(humidity_hourly[:7])
            else:
                humidity_data = pd.Series([weather.get('humidity', 0)]*7)
            if isinstance(rainfall_hourly, list) and len(rainfall_hourly) >= 7:
                rainfall_data = pd.Series(rainfall_hourly[:7])
            else:
                rainfall_data = pd.Series([weather.get('precipitation', 0)]*7)
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=date_range,
                y=temp_data,
                mode='lines+markers',
                name='Temperature',
                line=dict(color='#FF4B4B'),
                yaxis='y1'))
            fig.add_trace(go.Scatter(
                x=date_range,
                y=humidity_data,
                mode='lines+markers',
                name='Humidity',
                line=dict(color='#00CED1'),
                yaxis='y2'))
            fig.add_trace(go.Bar(
                x=date_range,
                y=rainfall_data,
                name='Rainfall',
                marker_color='#4169E1'))
            fig.update_layout(
                title='7-Day Weather Forecast',
                xaxis_title='Date',
                yaxis=dict(title='Temperature (°C)',titlefont=dict(color='#FF4B4B'),tickfont=dict(color='#FF4B4B'),side='left'),
                yaxis2=dict(title='Humidity (%)',titlefont=dict(color='#00CED1'),tickfont=dict(color='#00CED1'),overlaying='y',side='right'),
                legend=dict(orientation='h',yanchor='bottom',y=1.02,xanchor='right',x=1),
                margin=dict(l=50, r=50, t=50, b=50),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#333333'))
            fig.update_traces(
                hovertemplate='%{y:.1f} %{text}',
                text=['°C' if trace.name == 'Temperature' else '%' if trace.name == 'Humidity' else 'mm' for trace in fig.data])
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating weather graph: {e}")

        # Market Price Data
        st.subheader("Market Price Data")
        
        # Get crops for the region
        crops = region_crops.get(region, {}).get('crops', [])
        if not crops:
            st.error(f"No crops found for region: {region}")
            st.stop()
        


        # Display real market prices from WFP data
        from src.data_collection.market_price_processor import get_region_prices, format_market_conditions
        from datetime import datetime
        
        try:
            # Get market prices for the selected region
            region_prices = get_region_prices(region)
            
            if region_prices is not None and not region_prices.empty:
                # Format the data for display
                region_prices['Market Condition'] = region_prices['Market Condition'].apply(format_market_conditions)
                
                # Create a more user-friendly display
                st.write("\n")
                # Removed redundant subheader here
                # Add last updated timestamp
                last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.info(f"Last updated: {last_updated}")
                
                # Display the market prices
                st.dataframe(region_prices[['Crop', 'Current Price', 'Unit', 'Market Condition']], 
                           use_container_width=True)
                
                # Add explanations for market conditions
                st.markdown("""
                **Market Conditions:**
                - ✓ Stable: Prices are within normal range
                - ⚠️ Caution: Prices are showing some volatility
                - ⚠️ Alert: Prices are significantly higher than normal
                - ❌ Crisis: Prices are at critical levels
                """)
            else:
                st.warning(f"No market price data available for {region} at this time.")
        except Exception as e:
            st.error(f"Error displaying market prices: {e}")
            if market_data:
                market_df = format_market_data(market_data)
                
                # Display market prices with auto-refresh
                st.write("\n")
                st.subheader("Real-time Market Prices")
                
                # Add last updated timestamp
                last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                st.info(f"Last updated: {last_updated}")
                
                # Display the market prices
                st.dataframe(market_df, use_container_width=True)
                
                # Add auto-refresh button
                if st.button("🔄 Refresh Prices"):
                    market_df = format_market_data(get_real_time_market_prices())
                    st.dataframe(market_df, use_container_width=True)
            else:
                st.warning("Unable to fetch market prices at this time.")
        except Exception as e:
            st.error(f"Error displaying market prices: {e}")

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
            market_data = market_predictor.get_market_data(crop_name)
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
                temp_data = pd.Series([weather.get('temperature', 0)]*7)
            
            if isinstance(humidity_hourly, list) and len(humidity_hourly) >= 7:
                humidity_data = pd.Series(humidity_hourly[:7])
            else:
                humidity_data = pd.Series([weather.get('humidity', 0)]*7)
            
            if isinstance(rainfall_hourly, list) and len(rainfall_hourly) >= 7:
                rainfall_data = pd.Series(rainfall_hourly[:7])
            else:
                rainfall_data = pd.Series([weather.get('precipitation', 0)]*7)
            
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

    except Exception as e:
        st.error(f"Error fetching or displaying data: {e}")

    # Store city in session state
    st.session_state['selected_city'] = city


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

    # Step 3: Market Price Analysis
    # st.subheader("3. Market Price Analysis")  # Removed duplicate legacy section
    
    # Get region from session state
    region = st.session_state.get('selected_region')
    if not region:
        st.error("Please select a city first from the sidebar")
        st.stop()

    # Get recommended crops for the region
    recommended_crops = region_crops.get(region, []) if region else []
    if not recommended_crops:
        st.warning("No crop recommendations available for this region")
    else:
        st.subheader("3. Recommended Crops")
        for crop in recommended_crops:
            st.write(f"- {crop}")
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
        market_data = market_predictor.get_market_data(crop_name)
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

# --- REMOVE LEGACY/OLD Market Price Analysis Section BELOW THIS LINE ---
# (This block is now handled above, and should not be rendered twice)

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

# If no city or greenhouse size provided
if not city or not length or not width:
    st.warning("Please provide a city and greenhouse size to continue.")
    st.stop()

