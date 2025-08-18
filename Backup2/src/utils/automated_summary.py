def generate_summary(weather_summary, market_summary, crop_recommendations, planting_dates):
    """
    Generate a summary using a template-based approach.

    Parameters:
        weather_summary (str): Summary of weather data.
        market_summary (str): Summary of market trends.
        crop_recommendations (list): Recommended crops with scores/values.
        planting_dates (list): Suggested optimal planting dates.

    Returns:
        str: Generated summary text.
    """
    # Extract the top recommended crop
    if crop_recommendations:
        top_crop = crop_recommendations[0]
    else:
        top_crop = "No specific crop recommended"
    
    # Format the summary
    summary = (
        f"Based on current weather conditions and market trends, {top_crop} is recommended for planting. "
        f"The optimal planting dates are {', '.join(planting_dates)}. "
        f"This recommendation is based on favorable weather conditions and market demand."
    )
    
    return summary
