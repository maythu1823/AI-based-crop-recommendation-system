import requests
from typing import Any
from datetime import datetime, timedelta


def get_city_coordinates(city: str) -> tuple[float, float]:
    """Convert a Myanmar city name into latitude & longitude using Open-Meteo's geolocation API.
    Includes a fallback mechanism for known cities."""
    # Fallback coordinates for known cities
    city_coordinates = {
        "pyin oo lwin": (21.8959, 96.1219),
        "mandalay": (21.9759, 96.0880),
        "yangon": (16.8547, 96.1926),
        "mawlamyine": (16.4326, 98.0058),
        "naypyidaw": (19.7500, 96.1167),
        "taunggyi": (20.7432, 97.3739),
        "sittwe": (20.2250, 93.1000),
        "myitkyina": (25.3550, 97.4500),
        "kyaikto": (16.5000, 97.3000),
        "bago": (17.0000, 96.5000)
    }
    
    # Try to get coordinates from API first
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en"
        response = requests.get(geo_url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data and "results" in data and data["results"]:
            lat = data["results"][0]["latitude"]
            lon = data["results"][0]["longitude"]
            return lat, lon
        else:
            raise ValueError(f"City not found in Myanmar: {city}")

    except requests.RequestException as err:
        # If API fails, try to get coordinates from fallback dictionary
        city_lower = city.lower()
        if city_lower in city_coordinates:
            return city_coordinates[city_lower]
        else:
            raise RuntimeError(f"Geolocation error: {err}. Could not find coordinates for city: {city}")

    except Exception as e:
        raise RuntimeError(f"Unexpected error getting coordinates: {e}")


def get_open_meteo_weather(lat: float, lon: float) -> dict[str, Any]:
    """
    Fetch full weather details from Open-Meteo, including soil temperature, seasonal averages, and climate zones.
    Use comma-separated values for the 'hourly' and 'daily' parameters to avoid repeated keys.
    """
    url = "https://api.open-meteo.com/v1/forecast"

    # Simplified parameters to avoid 400 errors
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,winddirection_10m,soil_temperature_0cm,soil_moisture_0_1cm,evapotranspiration,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset",
        "timezone": "Asia/Yangon",
        "current_weather": True,
        "start_date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
        "end_date": datetime.now().strftime("%Y-%m-%d")
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Calculate seasonal averages; note that the calculation here is a placeholder,
        # using daily maximum temperatures and precipitation sums across the period.
        daily_data = data.get("daily", {})
        avg_temp = (
            sum(daily_data.get("temperature_2m_max", [0])) / len(daily_data.get("temperature_2m_max", [1]))
            if daily_data.get("temperature_2m_max") else None
        )
        avg_precip = (
            sum(daily_data.get("precipitation_sum", [0])) / len(daily_data.get("precipitation_sum", [1]))
            if daily_data.get("precipitation_sum") else None
        )

        hourly_data = data.get("hourly", {})
        return {
            "temp_max": daily_data.get("temperature_2m_max", [None])[0],
            "temp_min": daily_data.get("temperature_2m_min", [None])[0],
            "precipitation": daily_data.get("precipitation_sum", [None])[0],
            "humidity": hourly_data.get("relativehumidity_2m", [None])[0],
            "wind_speed": hourly_data.get("windspeed_10m", [None])[0],
            "wind_direction": hourly_data.get("winddirection_10m", [None])[0],
            "soil_temperature": hourly_data.get("soil_temperature_0cm", [None])[0],
            "soil_moisture": hourly_data.get("soil_moisture_0_1cm", [None])[0],
            "evaporation_rate": hourly_data.get("evapotranspiration", [None])[0],
            "sunrise": daily_data.get("sunrise", ["N/A"])[0],  # Get first day's sunrise
            "sunset": daily_data.get("sunset", ["N/A"])[0],    # Get first day's sunset
            "weather_code": hourly_data.get("weathercode", [None])[0],  # Get current weather code
            "climate_zone": "Tropical Monsoon"  # Placeholder: Implement actual classification if required
        }

    except requests.RequestException as err:
        raise RuntimeError(f"Failed to fetch weather data: {err}")
