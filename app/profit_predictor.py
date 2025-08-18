import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, Any, Optional
import os
import json
import pandas as pd

TIMELINE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'crop_timelines.json')
try:
    _TIMELINES = json.load(open(TIMELINE_PATH, 'r', encoding='utf-8'))
except FileNotFoundError:
    _TIMELINES = {}

def _get_growth_days(crop: str, default_days: int = 90) -> int:
    stages = _TIMELINES.get(crop.lower())
    if not stages:
        return default_days
    try:
        return int(sum(s.get('duration', 0) for s in stages)) or default_days
    except Exception:
        return default_days

def predict_profit(crop_name: str, yield_per_sqm: float, total_yield: float,
                  price_per_kg: float,
                  greenhouse_size: float,
                  daily_water_available: Optional[float] = None,
                  water_cost_per_liter: Optional[float] = None,
                  fertilizer_cost: Optional[float] = None) -> Dict[str, Any]:
    """
    Predict profit using a more detailed cost structure based on operational expenses.
    
    Args:
        crop_name: Name of the crop
        yield_per_sqm: Yield in kg per square meter
        total_yield: Total yield in kg
        price_per_kg: Price per kg in MMK
        greenhouse_size: Size of greenhouse in square meters (optional)
        daily_water_available: Daily water available in liters (optional)
        water_cost_per_liter: Cost of water per liter in MMK (optional)
        fertilizer_cost: Cost of fertilizer in MMK (optional)
        
    Returns:
        Dictionary containing predicted profit in MMK and other information
    """
    # Default values if not provided
    if water_cost_per_liter is None:
        water_cost_per_liter = 0.5  # MMK per liter
    
    if fertilizer_cost is None:
        # Flat fertilizer cost (MMK per m²·day)
        fertilizer_cost = 10
    
    if greenhouse_size is None:
        # Estimate greenhouse size from total yield and yield per sqm
        greenhouse_size = total_yield / yield_per_sqm if yield_per_sqm > 0 else 100
    
    CROP_GROWTH_DAYS = _get_growth_days(crop_name.lower())

    # If the caller provides their daily capacity, use it directly; otherwise fall back to
    # an agronomic estimate based on crop-specific rate × area.
    if daily_water_available is None:
        water_usage_rates = {
            "rice": 15, "paddy": 15, "maize": 8, "corn": 8, "soybean": 6, "cotton": 7,
            "groundnut": 5, "sorghum": 6, "millet": 5, "wheat": 7, "barley": 6,
            "tea": 8, "coffee": 9, "onion": 5, "watermelon": 10, "beans": 6,
            "lentil": 4, "pineapple": 7, "strawberry": 8, "coconut": 12, "mango": 9,
            "banana": 14, "palm oil": 15, "sugarcane": 12, "sunflower": 7, "vegetables": 7
        }
        water_usage_rate = water_usage_rates.get(crop_name.lower(), 8)  # L / m² / day
        daily_water_available = water_usage_rate * greenhouse_size

    # Total water for the growth cycle
    total_water_usage = daily_water_available * CROP_GROWTH_DAYS
    
    # Calculate total water cost
    total_water_cost = total_water_usage * water_cost_per_liter
    
    # Fertilizer cost: rate (MMK per m²-day) × area × crop-specific duration
    total_fertilizer_cost = fertilizer_cost * greenhouse_size * CROP_GROWTH_DAYS
    
    # Calculate total revenue
    total_revenue = total_yield * price_per_kg
    
    # Revert "Other Costs" to a percentage of total revenue, as requested.
    other_costs = total_revenue * 0.10
    
    # Create feature matrix for Linear Regression
    X = np.array([
        [total_revenue, total_water_cost, total_fertilizer_cost, other_costs]
    ])
    
    # Create target vector (profit)
    # For simplicity, we'll use a simple formula: revenue - costs
    base_profit = total_revenue - (total_water_cost + total_fertilizer_cost + other_costs)
    y = np.array([base_profit])
    
    # Create and fit Linear Regression model
    model = LinearRegression()
    model.fit(X, y)
    
    # Predict profit
    predicted_profit = model.predict(X)[0]
    
    # Add some random variation (±15%) to make it more realistic
    variation = 0.85 + np.random.random() * 0.3  # 0.85 to 1.15
    final_profit = predicted_profit * variation
    
    # Ensure profit is reasonable (can be negative for unprofitable scenarios)
    
    # Calculate profit per square meter
    profit_per_sqm = final_profit / greenhouse_size if greenhouse_size > 0 else 0
    
    # Calculate return on investment (ROI)
    total_costs = total_water_cost + total_fertilizer_cost + other_costs
    roi = (final_profit / total_costs) * 100 if total_costs > 0 else 0
    
    return {
        "crop_name": crop_name,
        "total_revenue": round(total_revenue, 2),  # MMK
        "total_costs": round(total_costs, 2), # MMK
        "total_water_cost": round(total_water_cost, 2),  # MMK
        "total_fertilizer_cost": round(total_fertilizer_cost, 2),  # MMK
        "other_costs": round(other_costs, 2),  # MMK
        "total_profit": round(final_profit, 2),  # MMK
        "profit_per_sqm": round(profit_per_sqm, 2),  # MMK per sq.m
        "roi": round(roi, 2),  # %
        "confidence": 0.75  # Fixed confidence for demonstration
    }