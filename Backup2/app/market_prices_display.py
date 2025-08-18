import streamlit as st
import pandas as pd

def show_market_prices(csv_path: str, num_crops: int = 5):
    """
    Display market price data for the top N crops from the given CSV file.
    """
    try:
        df = pd.read_csv(csv_path)
        # Pick the 5 most common crops (Commodity)
        top_crops = df['Commodity'].value_counts().head(num_crops).index.tolist()
        filtered_df = df[df['Commodity'].isin(top_crops)]
        # Sort by frequency and take top 5
        top_5_crops = filtered_df['Commodity'].value_counts().head(num_crops).index.tolist()
        final_df = filtered_df[filtered_df['Commodity'].isin(top_5_crops)]
        
        # Select only the columns we want
        selected_columns = ['Commodity', 'Price Date', 'Price', 'Unit', 'Currency']
        final_df = final_df[selected_columns]
        
        # Sort by commodity and date
        final_df = final_df.sort_values(['Commodity', 'Price Date'])
        
        # Show in a nice table
        st.subheader('Market Price Data (Top 5 Crops)')
        st.dataframe(final_df)
    except Exception as e:
        st.error(f"Could not load market prices: {e}")
