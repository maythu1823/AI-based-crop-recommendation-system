import numpy as np
from sklearn.linear_model import LinearRegression
from typing import Dict, Any, Optional

def predict_yield(crop_name: str, greenhouse_size: float, temperature: float, rainfall: float, humidity: float, base_yield_kg_per_sqm: Optional[float] = None) -> Dict[str, Any]:
    """
    Predict crop yield using a weighted factor model based on ideal climate conditions.
    
    Args:
        crop_name: Name of the crop
        greenhouse_size: Size of greenhouse in square meters
        temperature: Temperature in Celsius
        rainfall: Rainfall in mm
        humidity: Humidity percentage
        base_yield_kg_per_sqm: Optional base yield in kg per sq.m
        
    Returns:
        Dictionary containing predicted yield in kg per sq.m and other information
    """
    # Define base yield for each crop (kg per sq.m)
    # These are approximate values for demonstration purposes, adjusted for greenhouse potential
    base_yields = {
        "rice": 0.8, "paddy": 0.8, "maize": 1.0, "corn": 1.0, "soybean": 0.5, 
        "cotton": 0.4, "groundnut": 0.6, "sorghum": 0.8, "millet": 0.7, 
        "wheat": 0.9, "barley": 0.8, "tea": 0.5, "coffee": 0.4, "onion": 4.0, 
        "watermelon": 5.0, "beans": 1.2, "lentil": 0.4, "pineapple": 2.5, 
        "strawberry": 2.0, "coconut": 0.2, "mango": 1.2, "banana": 3.0, 
        "palm oil": 0.5, "sugarcane": 8.0, "sunflower": 0.7, "vegetables": 1.5
    }
    
    # Get base yield from the new parameter if provided, otherwise use the hardcoded dictionary
    if base_yield_kg_per_sqm is not None:
        base_yield = base_yield_kg_per_sqm
    else:
        base_yield = base_yields.get(crop_name.lower(), 0.5)
    
    # --- Weighted Factor Model for Yield Prediction ---
    # Define optimal conditions and weights for environmental factors
    optimal_temp = 25  # °C
    optimal_rainfall = 300  # mm
    optimal_humidity = 70  # %
    
    weights = {
        'temp': 0.5,      # Temperature is the most critical factor
        'rainfall': 0.3,
        'humidity': 0.2
    }
    
    # Normalize environmental factors based on deviation from optimal values
    # The closer to optimal, the closer the score is to 1.
    temp_score = max(0, 1 - abs(temperature - optimal_temp) / 15)  # Penalize larger deviations
    rainfall_score = max(0, 1 - abs(rainfall - optimal_rainfall) / 400)
    humidity_score = max(0, 1 - abs(humidity - optimal_humidity) / 30)

    # Calculate the overall yield factor using weighted scores
    yield_factor = (temp_score * weights['temp'] +
                    rainfall_score * weights['rainfall'] +
                    humidity_score * weights['humidity'])

    # The final yield is the base yield adjusted by the environmental factor
    # A small systematic variation is added for realism, but it's not random.
    final_yield = base_yield * yield_factor * 0.95  # Assume 95% of theoretical max
    
    # --- Dynamic Confidence Score ---
    # Confidence is the unweighted average of the environmental scores.
    # It reflects how suitable the current conditions are.
    confidence = np.mean([temp_score, rainfall_score, humidity_score])

    # Ensure yield is not negative
    final_yield = max(0, final_yield)

    # Calculate yield per square meter
    yield_per_sqm = final_yield
    
    # Calculate total yield for the greenhouse
    total_yield = yield_per_sqm * greenhouse_size
    
    return {
        "crop_name": crop_name,
        "yield_per_sqm": round(yield_per_sqm, 2),  # kg per sq.m
        "total_yield": round(total_yield, 2),  # kg total
        "greenhouse_size": greenhouse_size,  # sq.m
        "confidence": round(confidence, 2)  # Dynamic confidence score
    }