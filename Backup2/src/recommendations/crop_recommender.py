import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV


def load_crop_data(file_path: str) -> pd.DataFrame:
    """
    Load crop data from a CSV file.

    Expected columns in the CSV:
      - crop_name (or crop): Name of the crop.
      - optimal_temperature: Optimal temperature for the crop.
      - water_requirement: Water requirement for the crop.
      - market_demand: Market demand indicator.

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

    For each crop, this function:
      - Adds the constant weather_feature.
      - Adds the constant market_feature.
      - Creates a binary 'preferred_flag' which is 1 if the crop is in the user's preferred list, else 0.

    Parameters:
      crop_df (pd.DataFrame): The original crop data.
      weather_feature (float): Weather-related feature value.
      market_feature (float): Market-related feature value.
      preferred_crops (list): List of crop names preferred by the user.

    Returns:
      A new DataFrame with the engineered features.
    """
    df = crop_df.copy()
    # Rename 'crop' to 'crop_name' if necessary.
    if "crop_name" not in df.columns and "crop" in df.columns:
        df.rename(columns={"crop": "crop_name"}, inplace=True)

    df['weather_feature'] = weather_feature
    df['market_feature'] = market_feature
    df['preferred_flag'] = df['crop_name'].apply(lambda x: 1 if x in preferred_crops else 0)
    return df


def train_crop_recommender(crop_df: pd.DataFrame):
    """
    Trains a crop recommendation model using the engineered features.

    If a 'historical_yield' column is present in the DataFrame,
    the model converts it to a binary target (high yield vs low yield)
    based on the median value. Otherwise, a dummy target with random
    binary values is generated.

    A GridSearchCV is used to tune the hyperparameters of a RandomForestClassifier,
    improving model performance.

    Parameters:
      crop_df (pd.DataFrame): Crop data with engineered features.

    Returns:
      A trained RandomForestClassifier model (best estimator from GridSearchCV).
    """
    df = crop_df.copy()

    # Use real target if available; otherwise, create a dummy target.
    if 'historical_yield' in df.columns:
        threshold = df['historical_yield'].median()
        df['target'] = (df['historical_yield'] > threshold).astype(int)
    else:
        df['target'] = np.random.randint(0, 2, size=len(df))

    # Use only the engineered features for training.
    features = df[['weather_feature', 'market_feature', 'preferred_flag']]
    target = df['target']

    # Define hyperparameter grid for tuning.
    param_grid = {
        'n_estimators': [10, 50, 100],
        'max_depth': [None, 5, 10],
        'min_samples_split': [2, 5]
    }

    rf = RandomForestClassifier(random_state=42)
    # Update cv=2 (instead of 3) for cross-validation due to small dataset size.
    grid_cv = GridSearchCV(estimator=rf, param_grid=param_grid, cv=2, scoring='accuracy')
    grid_cv.fit(features, target)

    print("Best parameters for Crop Recommender:", grid_cv.best_params_)
    print("Best cross validation score:", grid_cv.best_score_)

    best_model = grid_cv.best_estimator_
    return best_model


def recommend_crops(model, features, top_n=3):
    """
    Provides crop recommendations based on the trained model.

    Since the model was trained using the features 'weather_feature',
    'market_feature', and 'preferred_flag', we only pass these columns
    to the model's predict_proba() method.

    Parameters:
      model: The trained crop recommendation model.
      features (pd.DataFrame): DataFrame with engineered features (and additional info).
      top_n (int): The number of top recommendations to return.

    Returns:
      A pandas Series containing the top recommended crop names.
    """
    # Use only the columns that were used for training.
    feature_cols = ['weather_feature', 'market_feature', 'preferred_flag']
    proba = model.predict_proba(features[feature_cols])

    # Check if only one probability column is available; otherwise, use column index 1.
    if proba.shape[1] == 1:
        scores = proba[:, 0]
    else:
        scores = proba[:, 1]

    features = features.copy()  # Avoid modifying the original DataFrame.
    features['score'] = scores
    recommended = features.sort_values(by='score', ascending=False).head(top_n)
    return recommended['crop_name']


# -----------------------------
# Test Block: Run the module directly
# -----------------------------
if __name__ == "__main__":
    # Compute the project root by going up three levels from the current file's directory.
    # Current file: ...\src\recommendations\crop_recommender.py
    # Project root should be: C:\Users\ASUS\Desktop\Python Project
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(project_root, "data", "raw", "crop_data.csv")

    print("Working directory:", os.getcwd())
    print("Loading crop data from:", file_path)

    # Load crop data.
    crop_df = load_crop_data(file_path)

    # Example parameters
    weather_feature = 5.0  # constant weather value for demonstration
    market_feature = 3.2  # constant market value for demonstration
    preferred_crops = ["Tomato", "Lettuce"]  # example preferred crops

    # Engineer features (this will also rename 'crop' to 'crop_name' if necessary)
    features_df = engineer_features(crop_df, weather_feature, market_feature, preferred_crops)

    # Train the crop recommender model.
    model = train_crop_recommender(features_df)

    # Get recommendations.
    recommendations = recommend_crops(model, features_df, top_n=3)
    print("Top Recommended Crops:")
    print(recommendations)
