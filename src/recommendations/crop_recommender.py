# File: src/recommendations/crop_recommender.py

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier


def load_crop_data(file_path: str) -> pd.DataFrame:
    """
    Load crop data from a CSV file.

    Expected columns in the CSV:
      - crop_name: Name of the crop.
      - climate_suitability: A measure (ideally numeric) indicating how well the crop fits local climates.
      - growth_cycle: Description or length of the crop’s growth cycle.

    Returns:
      A pandas DataFrame containing the crop data.
    """
    return pd.read_csv(file_path)


def engineer_features(crop_df: pd.DataFrame,
                      weather_feature: float,
                      market_feature: float,
                      preferred_crops: list) -> pd.DataFrame:
    """
    Engineers additional features for crop recommendation.

    For each crop in the DataFrame:
      - Adds the constant weather_feature from the current user input.
      - Adds the constant market_feature from the current user input.
      - Creates a binary 'preferred_flag' which is 1 if the crop is in the user's preferred list, else 0.

    Parameters:
      crop_df (pd.DataFrame): The original crop data.
      weather_feature (float): The feature value from weather data.
      market_feature (float): The feature value from market data.
      preferred_crops (list): List of crop names preferred by the user.

    Returns:
      A new DataFrame with the engineered features.
    """
    df = crop_df.copy()
    df['weather_feature'] = weather_feature
    df['market_feature'] = market_feature
    df['preferred_flag'] = df['crop_name'].apply(lambda x: 1 if x in preferred_crops else 0)
    return df


def train_crop_recommender(crop_df: pd.DataFrame):
    """
    Trains a crop recommendation model using the engineered features.

    Since historical performance labels might not be available immediately,
    a dummy target is generated for demonstration (random binary values).

    In practice, you would use target values derived from historical yield,
    profit or farmer satisfaction.

    Parameters:
      crop_df (pd.DataFrame): The crop data with engineered features.

    Returns:
      A trained RandomForestClassifier model.
    """
    df = crop_df.copy()
    # Create a dummy target column with random binary values.
    df['target'] = np.random.randint(0, 2, size=len(df))
    features = df[['weather_feature', 'market_feature', 'preferred_flag']]
    target = df['target']
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(features, target)
    return model


def recommend_crops(model, crop_df: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """
    Generates crop recommendations using the trained model.

    The model predicts a probability (score) for each crop, indicating its suitability.
    Crops are then ranked by the predicted score (in descending order) and the top_n rows are returned.

    Parameters:
      model: The trained crop recommender model.
      crop_df (pd.DataFrame): Crop data with engineered features.
      top_n (int): The number of top recommendations to return.

    Returns:
      A pandas DataFrame with the recommended crops and their corresponding score.
    """
    df = crop_df.copy()
    features = df[['weather_feature', 'market_feature', 'preferred_flag']]
    # Predict probability of the positive class (here, class 1)
    scores = model.predict_proba(features)[:, 1]
    df['score'] = scores
    recommended = df.sort_values(by='score', ascending=False).head(top_n)
    return recommended[['crop_name', 'score']]
