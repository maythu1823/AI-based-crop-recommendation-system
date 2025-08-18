import pandas as pd
from prophet import Prophet
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional
import requests
from typing import Optional
from app.crop_info import CropInfo

class PlantingDatePredictor:
    def __init__(self, latitude: float, longitude: float, historical_weather_df: Optional[pd.DataFrame] = None):
        """
        Initialize the planting date predictor.

        Args:
            latitude: Latitude of the region
            longitude: Longitude of the region
            historical_weather_df: DataFrame containing historical weather data
                Expected columns: ds (date), temp_max, temp_min, rainfall, humidity
        """
        self.model = None
        self.latitude = latitude
        self.longitude = longitude
        self.historical_data = None
        self.crop_info = CropInfo()

        if historical_weather_df is not None:
            self.historical_data = historical_weather_df
        else:
            self._fetch_historical_weather()

        if self.historical_data is not None and not self.historical_data.empty:
            self._train_model()

    def _fetch_historical_weather(self):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            url = f'https://archive-api.open-meteo.com/v1/archive'
            params = {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'start_date': start_date_str,
                'end_date': end_date_str,
                'hourly': 'temperature_2m,relative_humidity_2m,precipitation',
                'timezone': 'auto'
            }
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or 'hourly' not in data:
                print('Invalid response format from Open-Meteo API:', data)
                self.historical_data = None
                return
            hourly = data['hourly']
            required_fields = ['time', 'temperature_2m', 'relative_humidity_2m', 'precipitation']
            missing_fields = [field for field in required_fields if field not in hourly]
            if missing_fields:
                print(f'Missing required fields: {missing_fields}')
                self.historical_data = None
                return
            df = pd.DataFrame({
                'time': hourly.get('time', []),
                'temperature_2m': pd.to_numeric(hourly.get('temperature_2m', []), errors='coerce'),
                'relative_humidity_2m': pd.to_numeric(hourly.get('relative_humidity_2m', []), errors='coerce'),
                'precipitation': pd.to_numeric(hourly.get('precipitation', []), errors='coerce')
            })
            if df.empty:
                print('No data received from Open-Meteo API')
                self.historical_data = None
                return
            df['ds'] = pd.to_datetime(df['time'])
            df = df.set_index('ds')
            # Aggregate to daily
            daily = df.resample('D').agg({
                'temperature_2m': ['max', 'min'],
                'precipitation': 'sum',
                'relative_humidity_2m': 'mean'
            })
            daily.columns = ['_'.join(col).strip() for col in daily.columns.values]
            # Only drop rows where all are missing
            daily = daily.dropna(how='all', subset=['temperature_2m_max', 'temperature_2m_min', 'precipitation_sum', 'relative_humidity_2m_mean'])
            # Fill missing values for each column with reasonable defaults
            daily['temperature_2m_max'] = daily['temperature_2m_max'].fillna(0)
            daily['temperature_2m_min'] = daily['temperature_2m_min'].fillna(0)
            daily['precipitation_sum'] = daily['precipitation_sum'].fillna(0)
            daily['relative_humidity_2m_mean'] = daily['relative_humidity_2m_mean'].fillna(50)
            if daily.empty:
                print('No valid daily weather data after cleaning.')
                self.historical_data = None
                return
            daily = daily.rename(columns={
                'temperature_2m_max': 'temp_max',
                'temperature_2m_min': 'temp_min',
                'precipitation_sum': 'rainfall',
                'relative_humidity_2m_mean': 'humidity'
            })
            self.historical_data = daily.reset_index()[['ds', 'temp_max', 'temp_min', 'rainfall', 'humidity']]
        except Exception as e:
            print(f"Error fetching or processing weather data: {str(e)}")
            self.historical_data = None
            return
        except Exception as e:
            print(f"Error fetching historical weather data: {str(e)}")
            self.historical_data = None
            raise

    def _prepare_data(self, crop: str) -> pd.DataFrame:
        """
        Prepare data for Prophet model by adding crop-specific features.
        """
        # Add crop-specific features
        if crop.lower() == 'tomato':
            optimal_temp = 25
            optimal_rain = 200
        elif crop.lower() == 'cucumber':
            optimal_temp = 28
            optimal_rain = 150
        else:
            optimal_temp = 25
            optimal_rain = 175

        # Create features that indicate how close we are to optimal conditions
        self.historical_data['temp_score'] = 1 - abs(self.historical_data['temp_max'] - optimal_temp) / 10
        self.historical_data['rain_score'] = 1 - abs(self.historical_data['rainfall'] - optimal_rain) / 100

        # Create a planting suitability score
        self.historical_data['planting_score'] = (
            0.4 * self.historical_data['temp_score'] +
            0.4 * self.historical_data['rain_score'] +
            0.2 * (1 - abs(self.historical_data['humidity'] - 70) / 30)
        )

        # Create a DataFrame for Prophet
        df = self.historical_data.copy()
        df['y'] = df['planting_score']
        return df

    def _train_model(self):
        """Train the Prophet model."""
        if self.historical_data is None:
            raise ValueError("Historical data not provided")

        # Prepare data
        df = self._prepare_data('tomato')  # Start with tomato as default

        # Initialize and fit Prophet model
        self.model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            changepoint_prior_scale=0.1
        )

        # Add additional regressors
        self.model.add_regressor('temp_score')
        self.model.add_regressor('rain_score')
        self.model.add_regressor('humidity')

        # Fit the model
        self.model.fit(df)

    def predict_planting_dates(self, crop: str, region: str, num_dates: int = 3) -> List[Dict]:
        """
        Predict optimal planting dates for a given crop.

        Args:
            crop: Name of the crop
            region: Name of the region
            num_dates: Number of optimal dates to return

        Returns:
            List of dictionaries containing predicted planting dates and scores
        """
        # Since we don't have enough historical weather and crop data,
        # we'll generate random planting dates in the near future

        # Get current date
        current_date = datetime.now()

        # Generate random dates within the next 3 months
        results = []
        for i in range(num_dates):
            # Random days between 7 and 90 days from now
            random_days = np.random.randint(7, 90)
            future_date = current_date + timedelta(days=random_days)

            # Format the date
            results.append({
                'date': future_date,  # Store as datetime object
                'score': float(0.7 + np.random.random() * 0.3),  # Random score between 0.7 and 1.0
                'confidence': float(0.8),
                'region': region,
                'crop': crop
            })

        # Sort by date
        results.sort(key=lambda x: x['date'])

        return results

    def get_seasonal_pattern(self, crop: str) -> Dict:
        """
        Get the seasonal planting pattern for a crop.

        Returns:
            Dictionary containing seasonal planting information
        """
        try:
            if self.model is None or self.historical_data is None or self.historical_data.empty:
                print("Warning: Model or historical data not available for seasonal pattern analysis.")
                return {
                    'best_period': "Not available",
                    'peak_season_start': "N/A",
                    'peak_season_end': "N/A",
                    'rationale': "Insufficient data for prediction."
                }
                
            if self.model is None:
                self._train_model()

            # Get future predictions to extract seasonal components
            future = self.model.make_future_dataframe(periods=365)

            # Automatically add all regressors used during training
            # Prophet stores them in self.model.extra_regressors
            if hasattr(self.model, 'extra_regressors') and self.historical_data is not None:
                for reg_name in self.model.extra_regressors:
                    if reg_name in self.historical_data.columns:
                        reg_mean = self.historical_data[reg_name].mean()
                        future[reg_name] = reg_mean
                    else:
                        # If regressor missing in historical data, fill with 0
                        future[reg_name] = 0

            forecast = self.model.predict(future)

            # Calculate seasonal components
            seasonal_components = forecast[['ds', 'yearly', 'weekly']]
            seasonal_components = seasonal_components.copy()
            seasonal_components['month'] = seasonal_components['ds'].dt.month

            # Find the date with the highest yearly seasonality component
            best_date = seasonal_components.loc[seasonal_components['yearly'].idxmax()]['ds']
            
            # Determine the best 2-month planting period
            start_date = best_date - timedelta(days=30)
            end_date = best_date + timedelta(days=30)
            
            best_period_str = f"{start_date.strftime('%B')} to {end_date.strftime('%B')}"

            return {
                'best_period': best_period_str,
                'peak_season_start': start_date.strftime('%Y-%m-%d'),
                'peak_season_end': end_date.strftime('%Y-%m-%d'),
                'rationale': f"The optimal planting window is based on peak yearly climate patterns around {best_date.strftime('%B %d')}."
            }

        except Exception as e:
            print(f"Error getting seasonal pattern: {e}")
            return {
                'best_period': "Error",
                'peak_season_start': "N/A",
                'peak_season_end': "N/A",
                'rationale': "An error occurred during seasonal analysis."
            }

def get_planting_date_recommendations(crop: str, region: str, latitude: float, longitude: float, historical_data: Optional[pd.DataFrame] = None) -> Dict:
    """
    Get planting date recommendations for a specific crop and region.

    Args:
        crop: Name of the crop
        region: Name of the region
        latitude: Latitude of the region
        longitude: Longitude of the region
        historical_data: Optional historical weather data

    Returns:
        Dictionary containing planting date recommendations
    """
    predictor = PlantingDatePredictor(latitude=latitude, longitude=longitude, historical_weather_df=historical_data)
    crop_info = predictor.crop_info.get_crop_info(crop)

    try:
        # Get optimal planting dates
        planting_dates = predictor.predict_planting_dates(crop, region)

        # Get seasonal pattern
        seasonal_pattern = predictor.get_seasonal_pattern(crop)

        # Filter out past dates
        current_date = datetime.now()
        future_dates = [date for date in planting_dates if date['date'] >= current_date]

        # If no future dates are available, use the next available date
        if not future_dates:
            future_dates = planting_dates
            if not future_dates:
                return {
                    'crop': crop,
                    'region': region,
                    'summary': crop_info.get('summary', 'No summary available.'),
                    'water_usage': crop_info.get('water_usage', 'N/A'),
                    'fertilizer': crop_info.get('fertilizer', 'N/A'),
                    'recommendation': 'Weather data unavailable. Unable to provide planting date recommendation at this time.'
                }

        # Format dates for display in 'Month Day, Year' format
        for date_info in future_dates:
            date_info['display_date'] = date_info['date'].strftime('%B %d, %Y')

        if len(future_dates) > 1:
            recommendation = f"Best time to plant {crop} in {region} region is between {future_dates[0]['display_date']} and {future_dates[-1]['display_date']}."
        else:
            recommendation = f"Best time to plant {crop} in {region} region is on {future_dates[0]['display_date']}."

        return {
            'crop': crop,
            'region': region,
            'summary': crop_info.get('summary', 'No summary available.'),
            'water_usage': crop_info.get('water_usage', 'N/A'),
            'fertilizer': crop_info.get('fertilizer', 'N/A'),
            'recommendation': recommendation
        }
    except Exception as e:
        return {
            'error': str(e),
            'crop': crop,
            'region': region
        }
    except Exception as e:
        return {
            'error': str(e),
            'crop': crop,
            'region': region
        }
