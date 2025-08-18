import requests
import pandas as pd
from datetime import datetime, timedelta
# from .weather import get_city_coordinates # No longer needed

# Historical weather data endpoint
HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"

def fetch_historical_weather(lat: float, lon: float, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Fetches historical weather data for a given region (now using lat/lon) and date range.
    Parameters:
    - lat (float): Latitude of the location.
    - lon (float): Longitude of the location.
    - start_date (str): Start date in 'YYYY-MM-DD' format.
    - end_date (str): End date in 'YYYY-MM-DD' format.
    Returns:
    - pd.DataFrame: A DataFrame with historical weather data.
    """
    if not lat or not lon:
        print("Error: Latitude or Longitude is missing. Cannot fetch historical weather.")
        return pd.DataFrame()

    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "hourly": "relativehumidity_2m",
        "timezone": "Asia/Yangon"
    }
    try:
        response = requests.get(HISTORICAL_API_URL, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        
        # Prepare daily data
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        rainfall = daily.get("precipitation_sum", [])
        
        # Prepare average daily humidity from hourly data
        hourly = data.get("hourly", {})
        humidity = hourly.get("relativehumidity_2m", [])
        hourly_times = hourly.get("time", [])
        humidity_by_day = {}
        for t, h in zip(hourly_times, humidity):
            day = t[:10]
            if h is not None:  # Filter out None values
                humidity_by_day.setdefault(day, []).append(h)
        avg_humidity = [sum(humidity_by_day.get(d, [0])) / max(len(humidity_by_day.get(d, [])), 1) for d in dates]
        
        df = pd.DataFrame({
            "ds": dates,
            "temp_max": temp_max,
            "temp_min": temp_min,
            "rainfall": rainfall,
            "humidity": avg_humidity
        })
        return df
    except requests.exceptions.RequestException as e:
        print(f"Error fetching historical data for coords ({lat}, {lon}): {e}")
        return pd.DataFrame() # Return empty DataFrame on error

def get_planting_season_from_historical_data(region_name: str) -> dict:
    """
    Analyzes historical data to determine the optimal planting season for a given region.
    NOTE: This is a placeholder. A more sophisticated analysis would be needed for a real-world scenario.
    """
    # This function now needs coordinates. It cannot function with just region_name.
    # It will need to be refactored or removed if historical data is fetched differently.
    # For now, we will assume it's not the primary source of error and focus on the direct usage.
    # To make it runnable without erroring, we can't call get_city_coordinates.
    # This function is likely unused or will be called with lat/lon from another source.
    # lat, lon = get_city_coordinates(region_name)
    
    # Placeholder dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * 5) # 5 years of data
    
    # We cannot proceed without coordinates. This function is now broken.
    # It highlights the dependency that needs to be refactored in the calling code.
    print(f"WARNING: get_planting_season_from_historical_data for '{region_name}' cannot function without coordinates.")
    return {
        "Best Planting Start": "N/A",
        "Best Planting End": "N/A",
        "Reasoning": "Historical data analysis is currently disabled due to missing coordinates."
    }
    
    # The original logic is commented out below as it will fail.
    # historical_data = fetch_historical_weather(region_name, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    
    # if historical_data.empty:
    #     return {
    #         "Best Planting Start": "N/A",
    #         "Best Planting End": "N/A",
    #         "Reasoning": "Could not retrieve historical data."
    #     }
        
    # # Example analysis: find months with moderate temperature and rainfall
    # historical_data['month'] = pd.to_datetime(historical_data['time']).dt.month
    # monthly_avg = historical_data.groupby('month').mean()
    
    # # Find months with temperature between 15-30°C and low precipitation
    # suitable_months = monthly_avg[
    #     (monthly_avg['temperature_2m_mean'] > 15) &
    #     (monthly_avg['temperature_2m_mean'] < 30) &
    #     (monthly_avg['precipitation_sum'] < 100) # Example threshold for "low"
    # ]
    
    # if suitable_months.empty:
    #     return {
    #         "Best Planting Start": "N/A",
    #         "Best Planting End": "N/A",
    #         "Reasoning": "No ideal planting months found based on historical data."
    #     }
        
    # start_month = suitable_months.index.min()
    # end_month = suitable_months.index.max()
    
    # # Convert month number to month name
    # start_month_name = datetime.strptime(str(start_month), "%m").strftime("%B")
    # end_month_name = datetime.strptime(str(end_month), "%m").strftime("%B")

    # return {
    #     "Best Planting Start": start_month_name,
    #     "Best Planting End": end_month_name,
    #     "Reasoning": "Based on historical averages of moderate temperature and low rainfall."
    # }
