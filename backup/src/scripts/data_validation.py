# File: src/scripts/data_validation.py
# Description:
#   This script validates your CSV data files by loading them,
#   printing DataFrame information, descriptive statistics,
#   and counts of missing values.
#
# NEW FILE — Create this file under src/scripts/.

import os
import pandas as pd

# -----------------------------
# Compute the Project Root Directory
# -----------------------------
# This file is at: [project_root]/src/scripts/data_validation.py
# So we need to go up three levels to reach the project root.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Construct paths to the CSV files located at [project_root]/data/raw/
crop_data_path = os.path.join(project_root, "data", "raw", "crop_data.csv")
market_data_path = os.path.join(project_root, "data", "raw", "market_data.csv")


# -----------------------------
# Data Validation for Crop Data
# -----------------------------
def validate_crop_data(file_path: str):
    """
    Loads the crop data CSV file and prints:
      - DataFrame info (data types and non-null counts)
      - Descriptive statistics for all columns
      - Counts of missing values in each column
    """
    try:
        crop_df = pd.read_csv(file_path)
        print("==== Crop Data Information ====")
        crop_df.info()  # prints info to stdout
        print("\n=== Crop Data Summary (Descriptive Statistics) ===")
        print(crop_df.describe(include='all'))
        print("\n=== Missing Data in Crop File ===")
        print(crop_df.isnull().sum())
    except Exception as e:
        print("Error loading crop data:", e)


# -----------------------------
# Data Validation for Market Data
# -----------------------------
def validate_market_data(file_path: str):
    """
    Loads the market data CSV file (with date parsing) and prints:
      - DataFrame info
      - Descriptive statistics for numeric and non-numeric columns
      - Counts of missing values in each column
    """
    try:
        market_df = pd.read_csv(file_path, parse_dates=['date'])
        print("==== Market Data Information ====")
        market_df.info()
        print("\n=== Market Data Summary (Descriptive Statistics) ===")
        print(market_df.describe(include='all'))
        print("\n=== Missing Data in Market File ===")
        print(market_df.isnull().sum())
    except Exception as e:
        print("Error loading market data:", e)


# -----------------------------
# Main Function to Run All Validations
# -----------------------------
def main():
    print("Starting Data Validation...\n")

    print("Validating Crop Data...")
    validate_crop_data(crop_data_path)

    print("\nValidating Market Data...")
    validate_market_data(market_data_path)

    print("\nData Validation Completed.")


if __name__ == "__main__":
    main()
