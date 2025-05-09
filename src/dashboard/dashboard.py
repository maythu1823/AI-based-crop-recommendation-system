# File: src/dashboard/dashboard.py
import sys
import os

# Compute the project root directory (two levels up from dashboard.py)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.database.db import init_db, SessionLocal

init_db()  # Create tables if they don't exist
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Import modules from your project
from src.data_collection.weather import get_current_weather
from src.data_collection.market_data import load_market_data, preprocess_market_data
from src.recommendations.crop_recommender import load_crop_data, engineer_features, train_crop_recommender, \
    recommend_crops
from src.forecasting.planting_date_predictor import predict_optimal_planting_dates
from src.utils.automated_summary import generate_summary
from src.planning.resource_planner import train_yield_model, predict_yield, estimate_profit, simulate_resource_data, \
    train_resource_models, predict_resources
from src.planning.market_price_predictor import forecast_market_price

# --- Sidebar for User Inputs ---
st.sidebar.header("Greenhouse Settings")
location = st.sidebar.selectbox("Greenhouse Location", options=["Mandalay", "Yangon", "Naypyidaw", "Other"])
greenhouse_size = st.sidebar.number_input("Greenhouse Size (sq.m)", min_value=100, max_value=10000, value=1000,
                                          step=100)
weather_feature = st.sidebar.slider("Weather Feature Score", min_value=0.0, max_value=10.0, value=5.0, step=0.1)
market_feature = st.sidebar.slider("Market Feature Score", min_value=0.0, max_value=10.0, value=3.2, step=0.1)
water_availability = st.sidebar.number_input("Water Availability (liters per day)", min_value=0, value=1000, step=100)
fertilizer_type = st.sidebar.selectbox("Fertilizer Type", options=["Organic", "Chemical", "None"])
preferred_crops = st.sidebar.multiselect("Preferred Crops", options=["Tomato", "Lettuce", "Chili Pepper", "Cucumber"])

# --- Main Dashboard Content ---
st.title("Greenhouse Plant Planning Dashboard")

# --- Current Weather Data ---
location_coords = {
    "Mandalay": (21.9589, 96.0921),
    "Yangon": (16.8409, 96.1735),
    "Naypyidaw": (19.7633, 96.0785),
    "Other": (21.9589, 96.0921)
}
(lat, lon) = location_coords.get(location, (21.9589, 96.0921))
API_KEY = "511246d9c4eb776de4176959a5152030"
weather = get_current_weather(lat, lon, API_KEY)
st.header("Current Weather for " + location)
st.write(weather)

# --- Market Data ---
market_file = os.path.join(project_root, "data", "raw", "market_data.csv")
market_df = load_market_data(market_file)
if market_df is not None:
    market_df = preprocess_market_data(market_df)
    st.header("Market Data")
    st.write(market_df.head())
else:
    st.error("Failed to load market data. Please check file path and format.")

# --- Crop Recommendation ---
crop_file = os.path.join(project_root, "data", "raw", "crop_data.csv")
df_crop = load_crop_data(crop_file)
if df_crop is not None:
    features_df = engineer_features(df_crop, weather_feature, market_feature, preferred_crops)
    crop_model = train_crop_recommender(features_df)
    recommendations = recommend_crops(crop_model, features_df, top_n=3)
    st.header("Crop Recommendations")
    st.write(f"Weather Feature: {weather_feature}, Market Feature: {market_feature}")
    st.write("Top Recommended Crops:")
    st.write(recommendations)
else:
    st.error("Failed to load crop data. Please check file format and path.")

# --- Planting Date Prediction ---
st.header("Planting Date Prediction")
dates = pd.date_range(start='2025-01-01', periods=120)
temperatures = np.random.normal(loc=22, scale=3, size=120)
df_history = pd.DataFrame({'ds': dates, 'y': temperatures})
optimal_dates = predict_optimal_planting_dates(df_history)
st.write("Predicted optimal planting dates (temperature between 18°C and 25°C):")
st.write(optimal_dates)

# --- Automated Insights ---
weather_summary = f"Temperature: {weather.get('main', {}).get('temp', 'N/A')}°C, " \
                  f"{weather.get('weather', [{}])[0].get('description', 'N/A')}."
market_summary = "Market data indicates stable prices with slight growth for key crops."
ai_summary = generate_summary(weather_summary, market_summary, recommendations, optimal_dates)
st.header("Automated Insights")
st.write(ai_summary)

# --- Yield & Profit Prediction ---
st.header("Yield & Profit Prediction")
yield_model = train_yield_model()
# Update predict_yield call if necessary (ensure arguments match your function's signature)
predicted_yield = predict_yield(yield_model, greenhouse_size, weather_feature, market_feature)
estimated_profit = estimate_profit(predicted_yield, selling_price_per_kg=3.0, cost_factor=1000)
st.write(f"Predicted Yield (kg): {predicted_yield:.2f}")
st.write(f"Estimated Profit ($): {estimated_profit:.2f}")

# --- Market Price Prediction ---
st.header("Market Price Forecast")
if market_df is not None:
    market_prophet_df = market_df.copy()
    if "date" in market_prophet_df.columns:
        market_prophet_df.rename(columns={"date": "ds"}, inplace=True)
    if "price" in market_prophet_df.columns:
        market_prophet_df.rename(columns={"price": "y"}, inplace=True)
    market_forecast = forecast_market_price(market_prophet_df, period=30)
    st.write("Forecasted Market Prices:")
    st.write(market_forecast.tail(30))
    fig_market = px.line(market_forecast, x="ds", y="yhat", title="Market Price Forecast",
                         labels={"ds": "Date", "yhat": "Predicted Price"})
    st.plotly_chart(fig_market, key="market_forecast_chart")
else:
    st.error("Market data for forecasting is unavailable.")

# --- Resource Planning ---
st.header("Resource Planning")
resource_data = simulate_resource_data(num_samples=100)
resource_models = train_resource_models(resource_data)
resource_predictions = predict_resources(resource_models, greenhouse_size=greenhouse_size, yield_pred=predicted_yield,
                                         weather_feature=weather_feature)
st.write("Estimated Water Requirement (liters):", f"{resource_predictions['water_need']:.2f}")
st.write("Estimated Fertilizer Requirement (kg):", f"{resource_predictions['fertilizer_need']:.2f}")
st.write("Estimated Labor Requirement (hours):", f"{resource_predictions['labor_need']:.2f}")

# --- Database Test: Saving and Querying Weather Data ---
from src.database.db import WeatherData

session = SessionLocal()
weather_record = WeatherData(
    location=location,
    temperature=weather.get('main', {}).get('temp', 0),
    description=weather.get('weather', [{}])[0].get('description', "N/A")
)
session.add(weather_record)
session.commit()

queried_records = session.query(WeatherData).filter(WeatherData.location == location).all()
session.close()

st.header("Saved Weather Data for " + location)
for record in queried_records:
    st.write(f"Time: {record.timestamp}, Temp: {record.temperature}°C, Description: {record.description}")
# --- AI Chatbot (Optional Add-on) ---
import streamlit as st
from transformers import pipeline, Conversational

st.header("Chat with the AI Assistant")

# Initialize the chatbot only once and store it in session_state.
if "chatbot" not in st.session_state:
    with st.spinner("Loading chatbot model..."):
        st.session_state.chatbot = pipeline("conversational", model="microsoft/DialoGPT-medium")

# Text input for the user’s query.
# Using the older style if Conversation is not available.
user_query = st.text_input("Ask a question...", key="user_query_chatbot")
if user_query:
    # Create a conversational object (older style)
    conv = Conversational(user_query)
    with st.spinner("Generating response..."):
        output = st.session_state.chatbot(conv)
    # The response is typically in conv.generated_responses
    st.write("**AI Assistant:**", conv.generated_responses[-1])

