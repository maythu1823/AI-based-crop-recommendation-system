# File: src/planning/market_price_predictor.py

import pandas as pd
from prophet import Prophet


def forecast_market_price(df_market, period=30):
    """
    Forecast future market prices using the Prophet model.

    Parameters:
      df_market (pd.DataFrame): Historical market price data containing:
          - 'ds': datetime column (date of observation)
          - 'y': price of the crop

      period (int): Number of days to forecast into the future.

    Returns:
      pd.DataFrame: Forecast DataFrame with columns for date and predicted price (yhat).
    """
    # Initialize and fit the Prophet model on your market data.
    model = Prophet()
    model.fit(df_market)

    # Create a future dataframe extending by `period` days
    future = model.make_future_dataframe(periods=period)
    forecast = model.predict(future)

    # Usually, we are interested in the forecasted price (yhat)
    return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
