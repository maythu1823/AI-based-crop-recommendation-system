import streamlit as st
import math # Added for calculations
import os # For path operations in show_home_page
import base64 # For image encoding in show_home_page

# Function to load CSS files
def load_css(css_file):
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    css_path = os.path.join(project_root, css_file)
    if not os.path.isfile(css_path):
        # Fall back to original path if not found
        css_path = css_file
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

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

def get_weather_condition(weather_code):
    """Convert WMO weather code to human-readable condition with emoji"""
    weather_conditions = {
        0: "☀️ Clear Sky",
        1: "🌤️ Mainly Clear",
        2: "⛅ Partly Cloudy",
        3: "☁️ Overcast",
        45: "🌫️ Fog",
        48: "❄️ Depositing Rime Fog",
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
        71: "🌨️ Slight Snow Fall",
        73: "🌨️ Moderate Snow Fall",
        75: "🌨️ Heavy Snow Fall",
        77: "🌨️ Snow Grains",
        80: "🌧️ Slight Rain Showers",
        81: "🌧️ Moderate Rain Showers",
        82: "🌧️ Violent Rain Showers",
        85: "🌨️ Slight Snow Showers",
        86: "🌨️ Heavy Snow Showers",
        95: "⚡ Thunderstorm: Slight or moderate",
        96: "⚡ Thunderstorm with Slight Hail",
        99: "⚡ Thunderstorm with Heavy Hail"
    }
    return weather_conditions.get(weather_code, "🌈 Unknown Condition")

def get_water_recommendation(weather):
    """Get water recommendation based on weather conditions, including precipitation."""
    temp_max = weather.get('temp_max', 0)
    weather_code = weather.get('weather_code', 0)
    precipitation = weather.get('precipitation', 0) # Get current precipitation

    # If there's significant rainfall, recommend less or no additional watering
    if precipitation > 5:  # Threshold for significant rain, e.g., 5mm
        return {
            'amount': 0, # Or a very small amount
            'frequency': 'check soil moisture, likely no watering needed due to rain'
        }
    elif precipitation > 1: # Light rain
        return {
            'amount': 10, # Reduced amount
            'frequency': 'daily, adjust based on soil moisture'
        }

    # Original logic if no significant rain
    if temp_max > 30 or weather_code in [0, 1, 2]:  # Hot and Clear/Partly Cloudy
        return {
            'amount': 40,
            'frequency': 'daily'
        }
    elif temp_max < 20 or weather_code in [45, 48]:  # Cool and Foggy
        return {
            'amount': 20,
            'frequency': 'every 2 days'
        }
    else:  # Moderate conditions
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

def show_home_page():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_path = os.path.join(project_root, 'Home Page.jpg')
    if os.path.exists(img_path):
        with open(img_path, 'rb') as img_file:
            img_bytes = img_file.read()
            encoded = base64.b64encode(img_bytes).decode()
            st.markdown(
                f'''
                <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@800&display=swap" rel="stylesheet">
                <style>
                .stApp {{
                    background-image: url('data:image/jpeg;base64,{encoded}');
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }}
                /* ... existing CSS styles for glass-card, home-title, stButton etc. ... */
                .glass-card {{
                    background: rgba(255, 255, 255, 0.12);
                    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                    backdrop-filter: blur(10px);
                    -webkit-backdrop-filter: blur(10px);
                    border-radius: 22px;
                    padding: 2.5rem 2.7rem;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin-right: 10vw;
                    margin-left: auto;
                    margin-top: 9vh;
                    max-width: 540px;
                    min-width: 380px;
                }}
                .home-title {{
                    color: #f3f4f6;
                    font-family: 'Playfair Display', serif;
                    font-size: 2.9em;
                    font-weight: 800;
                    text-shadow: 0 4px 18px rgba(0,0,0,0.23);
                    text-align: center;
                    margin-bottom: 0;
                    line-height: 1.3;
                }}
                .stButton>button {{
                    background: linear-gradient(90deg,#34d399,#059669);
                    color: #fff;
                    font-weight: 700;
                    border: none;
                    border-radius: 9px;
                    padding: 0.9rem 2.7rem;
                    flex-direction: column;
                    align-items: flex-start;
                    font-size: 1.22rem;
                    box-shadow: 0 2px 10px rgba(52,211,153,0.13);
                    transition: all 0.18s cubic-bezier(.4,0,.2,1);
                }}
                .stButton>button:hover {{
                    background: linear-gradient(90deg,#059669,#34d399);
                    color: #f3f4f6;
                    transform: translateY(-2px) scale(1.04);
                }}
                </style>
                ''',
                unsafe_allow_html=True
            )
    # Glassmorphic card and centered button
    st.markdown(f'''
    <div class="glass-card">
        <div class="home-title">Welcome to Greenhouse Plant Planting System</div>
    </div>
    ''', unsafe_allow_html=True)
    # Button directly below and right-aligned with the card
    st.markdown('<div style="display:flex;justify-content:flex-end;margin-right:12vw;">', unsafe_allow_html=True)
    if st.button('Get Started →', key='get_started_btn'):
        st.session_state['show_dashboard'] = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # This will keep the home page shown until the button is clicked
    st.session_state['show_dashboard'] = False
    st.stop() 