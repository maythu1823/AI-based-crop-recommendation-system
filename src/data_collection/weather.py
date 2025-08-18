import requests
from typing import Any
from datetime import datetime, timedelta
import pytz
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def get_open_meteo_weather(lat: float, lon: float) -> dict[str, Any]:
    """
    Fetch full weather details from Open-Meteo, including soil temperature, seasonal averages, and climate zones.
    Use comma-separated values for the 'hourly' and 'daily' parameters to avoid repeated keys.
    Also fetches 7-day forecast data for visualization.
    """
    url = "https://api.open-meteo.com/v1/forecast"

    # Get today and 7 days in the future for forecast
    today = datetime.now()
    forecast_end_date = today + timedelta(days=7)

    # Simplified parameters to avoid 400 errors
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,relativehumidity_2m,windspeed_10m,winddirection_10m,soil_temperature_0cm,soil_moisture_0_1cm,evapotranspiration,weathercode,pressure_msl",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,sunrise,sunset,weathercode",
        "timezone": "Asia/Yangon",
        "current_weather": True,
        "start_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
        "end_date": forecast_end_date.strftime("%Y-%m-%d")
    }

    # Use a session with retry strategy
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504], connect=5)
    s.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        response = s.get(url, params=params, timeout=10)
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
        # Get the latest weather code from the hourly data
        weather_code = hourly_data.get('weathercode', [None])[-1] if hourly_data.get('weathercode') else None
        # Prepare 7-day forecast data
        forecast_dates = data.get("daily", {}).get("time", [])
        forecast_max_temps = daily_data.get("temperature_2m_max", [])
        forecast_min_temps = daily_data.get("temperature_2m_min", [])
        forecast_precipitation = daily_data.get("precipitation_sum", [])
        forecast_weather_codes = daily_data.get("weathercode", [])

        # Format dates for display
        formatted_dates = []
        for date_str in forecast_dates:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                formatted_dates.append(date_obj.strftime("%a, %b %d"))  # e.g., "Mon, Jan 01"
            except:
                formatted_dates.append(date_str)

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
            "pressure": hourly_data.get("pressure_msl", [None])[0],
            "sunrise": daily_data.get("sunrise", ["N/A"])[0],  # Get first day's sunrise
            "sunset": daily_data.get("sunset", ["N/A"])[0],    # Get first day's sunset
            "weather_code": weather_code,  # Use current hour's weather code
            "climate_zone": "Tropical Monsoon",  # Placeholder: Implement actual classification if required

            # 7-day forecast data
            "forecast": {
                "dates": formatted_dates,
                "max_temps": forecast_max_temps,
                "min_temps": forecast_min_temps,
                "precipitation": forecast_precipitation,
                "weather_codes": forecast_weather_codes
            }
        }

    except requests.RequestException as err:
        raise RuntimeError(f"Failed to fetch weather data: {err}")
