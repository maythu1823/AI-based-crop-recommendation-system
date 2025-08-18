import os
import pandas as pd


def load_market_data(file_path: str) -> pd.DataFrame:
    """
    Loads market data from a CSV file and returns a Pandas DataFrame.
    """
    try:
        data = pd.read_csv(file_path)
        print(f"Market data loaded successfully from {file_path}!")
        return data
    except Exception as e:
        print(f"Error loading market data: {e}")
        return None


def preprocess_market_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the market data DataFrame.
    """
    if "date" in df.columns:
        try:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
            df = df.dropna(subset=["date"])
        except Exception as e:
            print(f"Error processing date column: {e}")
    df = df.ffill()
    return df


if __name__ == "__main__":
    # Compute the absolute path to market_data.csv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate two levels up from src/data_collection/ to the project root.
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    file_path = os.path.join(project_root, "data", "raw", "market_data.csv")
    print("Computed file path:", file_path)

    df_market = load_market_data(file_path)

    if df_market is not None:
        print("Raw Market Data Preview:")
        print(df_market.head())

        processed_df = preprocess_market_data(df_market)
        print("\nProcessed Market Data Preview:")
        print(processed_df.head())
    else:
        print("Failed to load the market data. Please check the file path and format.")
