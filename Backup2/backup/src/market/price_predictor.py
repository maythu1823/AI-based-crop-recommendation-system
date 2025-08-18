import pandas as pd
from prophet import Prophet
from datetime import datetime
import numpy as np
from typing import List, Dict, Optional

class MarketPricePredictor:
    def __init__(self):
        self.models = {}
        self.data_path = None

    def set_data_path(self, data_path: str):
        """
        Set the path to the market data CSV file
        """
        self.data_path = data_path

    def load_market_data(self, data_path: str, region: str = None) -> pd.DataFrame:
        """
        Load and preprocess market price data
        Expected columns: 'date', 'region', 'crop_name', 'price_per_kg'
        """
        try:
            df = pd.read_csv(data_path)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Filter by region if specified
            if region:
                # Convert region to lowercase to match CSV format
                region = region.lower()
                df = df[df['region'] == region]
                if len(df) == 0:
                    raise ValueError(f"No market data found for region: {region}")
            
            return df
        except ValueError as ve:
            raise ValueError(f"Error loading market data: {str(ve)}")
        except Exception as e:
            raise Exception(f"Unexpected error loading market data: {str(e)}")

    def train_crop_model(self, df: pd.DataFrame, crop_name: str) -> Prophet:
        """
        Train a Prophet model for a specific crop's price prediction
        """
        try:
            # Filter data for specific crop
            crop_df = df[df['crop_name'] == crop_name]
            
            # Check if we have enough data points
            if len(crop_df) < 3:
                raise ValueError(f"Not enough data points for {crop_name}. Need at least 3 data points.")
                
            # Prepare data for Prophet
            prophet_df = pd.DataFrame({
                'ds': crop_df['date'],
                'y': crop_df['price_per_kg']
            })
            
            # Initialize and fit Prophet model with adjusted parameters for sparse data
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=False,  # Disable weekly seasonality for sparse data
                changepoint_prior_scale=0.5,  # Increase changepoint flexibility
                seasonality_prior_scale=10.0  # Increase seasonality flexibility
            )
            model.fit(prophet_df)
            
            return model
        except Exception as e:
            print(f"Error training model for {crop_name}: {str(e)}")
            raise

    def train_all_models(self, data_path: str, region: str = None) -> None:
        """
        Train price prediction models for all crops in the data
        """
        try:
            # Store the data path for future use
            self.set_data_path(data_path)
            
            df = self.load_market_data(data_path, region)
            
            # Get all unique crops in the data for this region
            crops = df['crop_name'].unique()
            
            # Train models for each crop
            for crop in crops:
                try:
                    model = self.train_crop_model(df, crop)
                    self.models[crop] = model
                except Exception as e:
                    print(f"Error training model for {crop}: {str(e)}")
                    continue
            
        except ValueError as ve:
            raise ValueError(f"Error loading market data: {str(ve)}")
        except Exception as e:
            raise Exception(f"Unexpected error training models: {str(e)}")

    def predict_prices(self, crop_name: str, days_ahead: int = 30, region: str = None) -> pd.DataFrame:
        """
        Predict future prices for a specific crop
        """
        if crop_name not in self.models:
            raise ValueError(f"No model trained for crop: {crop_name} in region: {region}")
            
        model = self.models[crop_name]
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(days_ahead)

    def get_price_trend(self, crop: str, days_ahead: int = 30, region: str = None) -> dict:
        """
        Get price trend prediction for a specific crop
        
        Args:
            crop: Name of the crop
            days_ahead: Number of days to predict ahead
            region: Optional region filter
            
        Returns:
            dict: Contains current price, predicted trend, and confidence
        """
        try:
            # Load data and filter by crop and region
            df = self.load_market_data(self.data_path, region)
            crop_df = df[df['crop_name'] == crop]
            
            if len(crop_df) == 0:
                raise ValueError(f"No market data found for crop: {crop} in region: {region}")
            
            # Get current price
            current_price = crop_df['price_per_kg'].iloc[-1]
            
            # Get historical trend
            last_30_days = crop_df.tail(30)
            price_change = (last_30_days['price_per_kg'].iloc[-1] - last_30_days['price_per_kg'].iloc[0]) / last_30_days['price_per_kg'].iloc[0]
            
            # Predict future trend
            model = self.models.get(crop)
            if model is None:
                # If no model exists, create a simple linear trend based prediction
                return {
                    'current_price': current_price,
                    'predicted_trend': price_change,  # Use historical trend as prediction
                    'confidence': abs(price_change)  # Higher absolute change = higher confidence
                }
            
            future = model.make_future_dataframe(periods=days_ahead)
            forecast = model.predict(future)
            
            # Calculate predicted trend
            predicted_change = (forecast['yhat'].iloc[-1] - forecast['yhat'].iloc[-days_ahead-1]) / forecast['yhat'].iloc[-days_ahead-1]
            
            return {
                'current_price': current_price,
                'predicted_trend': predicted_change,
                'confidence': model.model.score(crop_df['ds'], crop_df['y'])
            }
            
        except ValueError as ve:
            raise ValueError(f"Error getting price trend for {crop}: {str(ve)}")
        except Exception as e:
            raise Exception(f"Unexpected error getting price trend for {crop}: {str(e)}")
            raise

    def get_optimal_crop(self, crops: List[str], days_ahead: int = 30) -> Dict:
        """
        Get the most profitable crop based on price trend analysis
        """
        results = []
        
        for crop in crops:
            try:
                result = self.get_price_trend(crop, days_ahead)
                results.append({
                    'crop': crop,
                    'trend': result['predicted_trend'],
                    'confidence': result['confidence'],
                    'current_price': result['current_price']
                })
            except Exception as e:
                print(f"Error processing {crop}: {e}")
                continue
        
        # Sort by current price and confidence
        results.sort(key=lambda x: (x['current_price'] * x['confidence']), reverse=True)
        
        return results

# Example usage
if __name__ == "__main__":
    predictor = MarketPricePredictor()
    predictor.train_all_models("data/market_prices.csv")  # You'll need to create this file
    
    # Example prediction
    forecast = predictor.predict_prices("tomato", days_ahead=30)
    print("\nTomato Price Forecast:")
    print(forecast)
    
    # Example trend analysis
    trend = predictor.get_price_trend("tomato", days_ahead=30)
    print("\nTomato Price Trend:")
    print(trend)
    
    # Example optimal crop selection
    crops = ["tomato", "cucumber", "lettuce"]  # Example crops
    optimal = predictor.get_optimal_crop(crops)
    print("\nOptimal Crop Selection:")
    print(optimal)
