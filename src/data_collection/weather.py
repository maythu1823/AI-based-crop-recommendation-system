import requests
import os


def get_current_weather(lat: float, lon: float, api_key: str):
    """
    Fetch current weather conditions from OpenWeather using the current weather endpoint.

    Parameters:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
        api_key (str): Your OpenWeather API key.

    Returns:
        dict: JSON response with current weather data.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Will raise an error for a non-200 status code.
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching current weather data: {e}")
        return None


if __name__ == "__main__":
    # Ensure you have set your API key correctly.
    # You can either set it as an environment variable (OPENWEATHER_API_KEY) or replace the string below directly.
    api_key = os.getenv("511246d9c4eb776de4176959a5152030", "00f2dd74e05dfbbed4a679724d999b67")
    latitude = 21.9589
    longitude = 96.0921

    weather_data = get_current_weather(latitude, longitude, api_key)
    if weather_data:
        print("Current weather data fetched successfully!")
        print(weather_data)
    else:
        print("Failed to fetch current weather data.")
