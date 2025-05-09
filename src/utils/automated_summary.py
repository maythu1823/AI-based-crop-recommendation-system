from transformers import pipeline

# Initialize the text-generation pipeline using GPT-2 model.
text_generator = pipeline("text-generation", model="gpt2")


def generate_summary(weather_summary, market_summary, crop_recommendations, planting_dates):
    """
    Uses Hugging Face Transformers to generate an automated summary.

    Parameters:
        weather_summary (str): Summary of weather data.
        market_summary (str): Summary of market trends.
        crop_recommendations (list): Recommended crops with scores/values.
        planting_dates (list): Suggested optimal planting dates.

    Returns:
        str: Generated summary text.
    """
    prompt = (
        f"Based on the following information:\n"
        f"- Weather: {weather_summary}\n"
        f"- Market Trends: {market_summary}\n"
        f"- Crop Recommendations: {crop_recommendations}\n"
        f"- Optimal Planting Dates: {planting_dates}\n\n"
        "Please provide a concise, three-sentence summary advising a farmer on which crop to plant, "
        "when to plant it, and why these suggestions make sense."
    )

    generated = text_generator(prompt, max_new_tokens=50, do_sample=True, temperature=0.7)
    summary = generated[0]['generated_text']
    return summary
