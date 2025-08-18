import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from typing import Dict, Any

class MarketPricePredictor:
    def __init__(self):
        self.models = {}
        self.data_path = None

    def set_data_path(self, path: str):
        self.data_path = path

    def train_all_models(self, data_path: str, region: str):
        """Train models for all crops in the specified region"""
        try:
            # Load market data
            df = pd.read_csv(data_path)
            
            # Filter by region
            region_df = df[df['region'].str.lower() == region.lower()]
            
            # Get unique crops
            crops = region_df['crop'].unique()
            
            # Train model for each crop
            for crop in crops:
                crop_df = region_df[region_df['crop'] == crop]
                
                # Create features and target
                X = crop_df[['temperature', 'humidity', 'rainfall', 'month']].values
                y = crop_df['price'].values
                
                # Train model
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X, y)
                
                # Store model
                self.models[crop.lower()] = model
                
            return True
            
        except Exception as e:
            print(f"Error training models: {str(e)}")
            return False

    def get_price_trend(self, crop: str, days_ahead: int, region: str) -> Dict[str, Any]:
        """Get price trend prediction for a specific crop"""
        try:
            # Get model for the crop
            model = self.models.get(crop.lower())
            if not model:
                return {
                    'current_price': 0,
                    'predicted_trend': 0,
                    'confidence': 0
                }

            # Generate features for prediction
            # For demonstration, using random values
            current_price = np.random.uniform(100, 500)
            
            # Generate random trend (should be based on actual data)
            predicted_trend = np.random.uniform(-0.1, 0.1)
            confidence = np.random.uniform(0.6, 0.9)

            return {
                'current_price': current_price,
                'predicted_trend': predicted_trend,
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"Error getting price trend: {str(e)}")
            return {
                'current_price': 0,
                'predicted_trend': 0,
                'confidence': 0
            }
