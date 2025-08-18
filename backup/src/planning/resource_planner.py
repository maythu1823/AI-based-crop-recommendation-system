# File: src/planning/resource_planner.py

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression


# --- Resource Planning Functions ---

def simulate_resource_data(num_samples: int = 100):
    """
    Simulate historical resource usage data for resource planning.

    Returns a DataFrame with the following columns:
      - greenhouse_size: Size of the greenhouse in square meters.
      - yield: Simulated yield (kg). This might represent total yield or yield per unit area.
      - weather_feature: A simulated numerical weather index.
      - water_usage: Simulated water usage (liters per day).
      - fertilizer_usage: Simulated fertilizer usage (kg per day).
      - labor_hours: Simulated labor hours (hours per day).
    """
    # Simulate input features
    greenhouse_sizes = np.random.uniform(500, 2000, num_samples)  # square meters
    yields = np.random.uniform(100, 500, num_samples)  # yield in kg (for demonstration)
    weather_features = np.random.uniform(3, 10, num_samples)  # an abstract weather metric

    # Simulate resource usage; these relationships are illustrative.
    water_usage = 0.5 * greenhouse_sizes + 0.1 * yields + np.random.normal(0, 50, num_samples)
    fertilizer_usage = 0.05 * greenhouse_sizes + 0.05 * yields + np.random.normal(0, 5, num_samples)
    labor_hours = 0.01 * greenhouse_sizes + 0.2 * yields + np.random.normal(0, 10, num_samples)

    data = {
        'greenhouse_size': greenhouse_sizes,
        'yield': yields,
        'weather_feature': weather_features,
        'water_usage': water_usage,
        'fertilizer_usage': fertilizer_usage,
        'labor_hours': labor_hours
    }

    df = pd.DataFrame(data)
    return df


def train_resource_models(df: pd.DataFrame):
    """
    Trains regression models for predicting resource usage:
      - Water usage (liters per day)
      - Fertilizer usage (kg per day)
      - Labor hours (hours per day)

    The models use 'greenhouse_size', 'yield', and 'weather_feature' as predictors.

    Returns a dictionary with keys "water_model", "fertilizer_model", and "labor_model".
    """
    features = df[['greenhouse_size', 'yield', 'weather_feature']]
    water_target = df['water_usage']
    fertilizer_target = df['fertilizer_usage']
    labor_target = df['labor_hours']

    water_model = LinearRegression().fit(features, water_target)
    fertilizer_model = LinearRegression().fit(features, fertilizer_target)
    labor_model = LinearRegression().fit(features, labor_target)

    return {
        "water_model": water_model,
        "fertilizer_model": fertilizer_model,
        "labor_model": labor_model
    }


def predict_resources(models: dict, greenhouse_size: float, yield_pred: float, weather_feature: float):
    """
    Predicts resource requirements using trained models.

    Parameters:
        models (dict): Dictionary containing "water_model", "fertilizer_model", and "labor_model".
        greenhouse_size (float): Size of the greenhouse in square meters.
        yield_pred (float): Predicted yield (kg).
        weather_feature (float): A representative weather metric.

    Returns:
        dict: Predicted values for water_need (liters), fertilizer_need (kg), and labor_need (hours).
    """
    input_data = pd.DataFrame({
        'greenhouse_size': [greenhouse_size],
        'yield': [yield_pred],
        'weather_feature': [weather_feature]
    })

    water_need = models["water_model"].predict(input_data)[0]
    fertilizer_need = models["fertilizer_model"].predict(input_data)[0]
    labor_need = models["labor_model"].predict(input_data)[0]

    return {
        "water_need": water_need,
        "fertilizer_need": fertilizer_need,
        "labor_need": labor_need
    }


# --- Yield & Profit Prediction Functions ---

def train_yield_model():
    df = simulate_resource_data(num_samples=100)
    # Use greenhouse_size, weather_feature, and add market_feature (here we simulate it)
    # For demonstration, let’s simulate a market feature as random data
    df['market_feature'] = np.random.uniform(3, 10, len(df))
    X = df[['greenhouse_size', 'weather_feature', 'market_feature']]
    y = df['yield']
    model = LinearRegression().fit(X, y)
    return model

def predict_yield(model, greenhouse_size: float, weather_feature: float, market_feature: float):
    import pandas as pd
    input_data = pd.DataFrame({
        'greenhouse_size': [greenhouse_size],
        'weather_feature': [weather_feature],
        'market_feature': [market_feature]
    })
    predicted_yield = model.predict(input_data)[0]
    return predicted_yield



def estimate_profit(predicted_yield, selling_price_per_kg=3.0, cost_factor=1000):
    """
    Estimates profit based on the predicted yield.

    Parameters:
        predicted_yield (float): Predicted yield (kg).
        selling_price_per_kg (float): Assumed selling price per kg.
        cost_factor (float): Overall cost factor (e.g., cost for water/fertilizer/labor).

    Returns:
        float: Estimated profit.
    """
    profit = predicted_yield * selling_price_per_kg - cost_factor
    return profit
