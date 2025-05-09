import pandas as pd
from prophet import Prophet


def predict_optimal_planting_dates(df_weather):
    """
    Predicts optimal planting dates based on historical weather data.
    Expects df_weather to have:
      - 'ds': datetime column
      - 'y': a key metric (e.g., temperature)

    Returns:
      A list of predicted optimal planting dates.
    """
    # Initialize and fit the Prophet model
    m = Prophet()
    m.fit(df_weather)
    # Create a dataframe to hold predictions for the next 30 days
    future = m.make_future_dataframe(periods=30)
    forecast = m.predict(future)

    # For this example, we'll assume that an ideal planting window is when
    # the forecasted temperature is between 18 and 25 °C.
    optimal_dates = forecast[(forecast['yhat'] >= 18) & (forecast['yhat'] <= 25)]

    # Return the first three suitable dates as a list
    return optimal_dates['ds'].head(3).tolist()


if __name__ == "__main__":
    # Example: Simulate historical temperature data for the last 120 days.
    import numpy as np

    rng = pd.date_range(start='2025-01-01', periods=120)
    # Simulate temperature: normally distributed around 22°C with some variance.
    temp = np.random.normal(loc=22, scale=3, size=120)
    df_history = pd.DataFrame({'ds': rng, 'y': temp})

    dates = predict_optimal_planting_dates(df_history)
    print("Predicted optimal planting dates:", dates)
