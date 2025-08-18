import datetime
from typing import Dict, Optional

def calculate_sunlight_hours(weather_data: Dict) -> Optional[float]:
    """Calculate sunlight hours from sunrise and sunset times"""
    try:
        sunrise = weather_data.get('sunrise', '06:00')
        sunset = weather_data.get('sunset', '18:00')
        
        # Calculate sunlight hours
        sunlight_hours = (datetime.datetime.strptime(sunset, '%H:%M') - 
                        datetime.datetime.strptime(sunrise, '%H:%M')).seconds / 3600
        return sunlight_hours
    except Exception as e:
        print(f"Error calculating sunlight hours: {e}")
        return None

def get_weather_metrics(weather_data: Dict) -> Optional[Dict]:
    """Extract and format weather metrics from weather data"""
    if not weather_data or 'current_weather' not in weather_data:
        return None
    
    current_weather = weather_data['current_weather']
    try:
        return {
            'temperature': current_weather.get('temperature', 'N/A'),
            'weathercode': current_weather.get('weathercode', 'N/A'),
            'windspeed': current_weather.get('windspeed', 'N/A'),
            'winddirection': current_weather.get('winddirection', 'N/A'),
            'humidity': current_weather.get('relativehumidity_2m', 'N/A'),
            'dewpoint': current_weather.get('dewpoint_2m', 'N/A'),
            'pressure': current_weather.get('pressure_msl', 'N/A'),
            'cloudcover': current_weather.get('cloudcover', 'N/A'),
            'time': current_weather.get('time', 'N/A')
        }
    except Exception as e:
        print(f"Error extracting weather metrics: {e}")
        return None
