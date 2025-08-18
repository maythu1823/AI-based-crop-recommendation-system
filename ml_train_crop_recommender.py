import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

# Load full region-crop dataset with water_availability and fertilizer_type
crop_df = pd.read_csv('data/crop_data_with_region_full_v2.csv')
# Load market price data (use latest price for each crop/region)
market_df = pd.read_csv('data/market_prices.csv')

# Get latest price for each crop (by region)
market_df['date'] = pd.to_datetime(market_df['date'], errors='coerce')
latest_prices = market_df.sort_values('date').groupby(['region', 'crop_name']).tail(1)

# Merge crop data with price info (on crop_name), but keep only the region from crop_df
merged = pd.merge(crop_df, latest_prices[['crop_name', 'price_per_kg']], on='crop_name', how='left')

# Fill missing price_per_kg with a default value
merged['price_per_kg'] = merged['price_per_kg'].fillna(1000)

# Only drop rows with missing essential features (not price)
merged = merged.dropna(subset=['region', 'crop_name', 'optimal_temperature', 'optimal_rainfall', 'optimal_humidity'])

# Encode categorical features
le_region = LabelEncoder()
merged['region_enc'] = le_region.fit_transform(merged['region'])

# Encode fertilizer_type: 1 for organic, 0 for chemical/both
merged['fertilizer_type_enc'] = merged['fertilizer_type'].apply(lambda x: 1 if str(x).lower() == 'organic' else 0)

# Features: region, optimal_temperature, optimal_rainfall, optimal_humidity, price_per_kg, water_availability, fertilizer_type
X = merged[['region_enc', 'optimal_temperature', 'optimal_rainfall', 'optimal_humidity', 'price_per_kg', 'water_availability', 'fertilizer_type_enc']]
# Target: crop_name
le_crop = LabelEncoder()
y = le_crop.fit_transform(merged['crop_name'])

# Train/test split (for future evaluation)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Save model and encoders
joblib.dump(clf, 'ml_crop_recommender.pkl')
joblib.dump(le_region, 'ml_region_encoder.pkl')
joblib.dump(le_crop, 'ml_crop_encoder.pkl')

print('ML crop recommendation model trained and saved.')
