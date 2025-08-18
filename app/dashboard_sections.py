import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import os
import json
import re
from datetime import datetime, timedelta
import math
from app.ui_helpers import fmt, get_weather_condition
import base64
from app.profit_predictor import predict_profit

PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    with open(os.path.join(PROJECT_ROOT_DIR, "data", "crop_timelines.json"), "r", encoding="utf-8") as _f:
        CROP_TIMELINES_DATA = json.load(_f)
except Exception:
    CROP_TIMELINES_DATA = {}

def display_weather_information(st_obj, weather_data):
    st_obj.subheader("☁️ Weather Information")

    weather_container = st_obj.container()
    with weather_container:
        if not weather_data: # Check if weather data is available
            st_obj.warning("Weather data is not currently available.")
        else:
            weather_code = weather_data.get('weather_code', 0)
            weather_condition_str = get_weather_condition(weather_code)
            emoji, description = (weather_condition_str.split(' ', 1) if ' ' in weather_condition_str
                                  else ('🌈', weather_condition_str))

            dewpoint = weather_data.get('dewpoint')
            temp_c_val_for_dew = weather_data.get('temp', weather_data.get('temp_min'))
            humidity_val_for_dew = weather_data.get('humidity')

            if dewpoint is None:
                if isinstance(temp_c_val_for_dew, (int, float)) and \
                   isinstance(humidity_val_for_dew, (int, float)) and humidity_val_for_dew > 0:
                    try:
                        a, b = 17.27, 237.7
                        alpha = ((a * temp_c_val_for_dew) / (b + temp_c_val_for_dew)) + math.log(humidity_val_for_dew / 100.0)
                        calculated_dewpoint = (b * alpha) / (a - alpha)
                        dewpoint = calculated_dewpoint
                    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
                        dewpoint = temp_c_val_for_dew if isinstance(temp_c_val_for_dew, (int, float)) else "N/A"
                elif isinstance(temp_c_val_for_dew, (int, float)):
                    dewpoint = temp_c_val_for_dew
                else:
                    dewpoint = "N/A"
            elif not isinstance(dewpoint, (int, float)):
                dewpoint = "N/A"
            
            metrics_to_display = [
                {'icon': '🌡️', 'label': 'Maximum', 'value': fmt(weather_data.get('temp_max'), "°C")},
                {'icon': '🌡️', 'label': 'Minimum', 'value': fmt(weather_data.get('temp_min'), "°C")},
                {'icon': '💧', 'label': 'Dew Point', 'value': fmt(dewpoint, "°C")},
                {'icon': '🌱', 'label': 'Soil Temp', 'value': fmt(weather_data.get('soil_temperature'), "°C")},
                {'icon': '💨', 'label': 'Wind Speed', 'value': fmt(weather_data.get('wind_speed'), " km/h")},
                {'icon': '🧭', 'label': 'Wind Dir.', 'value': fmt(weather_data.get('wind_direction'), "°")},
                {'icon': ' barometer', 'label': 'Pressure', 'value': fmt(weather_data.get('pressure'), " hPa")},
                {'icon': '💦', 'label': 'Humidity', 'value': fmt(weather_data.get('humidity'), "%")},
                {'icon': '🌧️', 'label': 'Precipitation', 'value': fmt(weather_data.get('precipitation'), "mm")},
                {'icon': '🌿', 'label': 'Soil Moisture', 'value': fmt(weather_data.get('soil_moisture'), "%")},
                {'icon': emoji, 'label': 'Condition', 'value': description},
                {'icon': '🌅', 'label': 'Sunrise', 'value': weather_data.get('sunrise', 'N/A')[-8:] if isinstance(weather_data.get('sunrise'), str) and len(weather_data.get('sunrise', '')) >= 8 else weather_data.get('sunrise', 'N/A')},
                {'icon': '🌇', 'label': 'Sunset', 'value': weather_data.get('sunset', 'N/A')[-8:] if isinstance(weather_data.get('sunset'), str) and len(weather_data.get('sunset', '')) >= 8 else weather_data.get('sunset', 'N/A')},
                {'icon': '🌍', 'label': 'Climate Zone', 'value': weather_data.get('climate_zone', 'N/A')}
            ]

            col_left, col_right = st_obj.columns(2)
            columns = [col_left, col_right]

            for i, metric_data in enumerate(metrics_to_display):
                with columns[i % 2]:
                    card_html = f"""
                    <div class='individual-metric-card'>
                        <span class='metric-icon'>{metric_data['icon']}</span>
                        <span class='metric-label'>{metric_data['label']}</span>
                        <span class='metric-value'>{metric_data['value']}</span>
                    </div>
                    """
                    st_obj.markdown(card_html, unsafe_allow_html=True)

def display_forecast_graph(st_obj, weather_data, go_obj):
    st_obj.markdown("<div class='forecast-section-wrapper'>", unsafe_allow_html=True)
    if 'forecast' in weather_data and all(key in weather_data['forecast'] for key in ['dates', 'max_temps', 'min_temps', 'precipitation', 'weather_codes']):
        forecast = weather_data['forecast']

        fig = go_obj.Figure()

        fig.add_trace(go_obj.Scatter(
            x=forecast['dates'],
            y=forecast['max_temps'],
            mode='lines+markers',
            name='Max Temperature (°C)',
            line=dict(color='#FF5733', width=4, shape='spline', smoothing=1.3),
            marker=dict(size=10, symbol='circle', line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>Max Temp: %{y:.1f}°C<extra></extra>'
        ))

        fig.add_trace(go_obj.Scatter(
            x=forecast['dates'],
            y=forecast['min_temps'],
            mode='lines+markers',
            name='Min Temperature (°C)',
            line=dict(color='#3366FF', width=4, shape='spline', smoothing=1.3),
            marker=dict(size=10, symbol='circle', line=dict(width=2, color='white')),
            hovertemplate='<b>%{x}</b><br>Min Temp: %{y:.1f}°C<extra></extra>'
        ))

        fig.add_trace(go_obj.Bar(
            x=forecast['dates'],
            y=forecast['precipitation'],
            name='Precipitation (mm)',
            marker_color='rgba(73, 175, 255, 0.7)',
            opacity=0.8,
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Precipitation: %{y:.1f}mm<extra></extra>'
        ))

        fig.add_trace(go_obj.Scatter(
            x=forecast['dates'] + forecast['dates'][::-1],
            y=forecast['max_temps'] + forecast['min_temps'][::-1],
            fill='toself',
            fillcolor='rgba(100, 170, 255, 0.2)',
            line=dict(color='rgba(255, 255, 255, 0)'),
            hoverinfo='skip',
            showlegend=False
        ))

        weather_icons = []
        for code in forecast['weather_codes']:
            condition = get_weather_condition(code) 
            if condition and ' ' in condition:
                icon, _ = condition.split(' ', 1)
                weather_icons.append(icon)
            else:
                weather_icons.append('🌈')

        fig.update_layout(
            title={
                'text': '7-Day Weather Forecast',
                'font': {'size': 24, 'color': '#2C3E50', 'family': 'Arial, sans-serif'},
                'y': 0.95
            },
            xaxis={
                'title': {
                    'text': 'Date',
                    'font': {'size': 16, 'color': '#34495E'}
                },
                'tickfont': {'size': 14},
                'gridcolor': 'rgba(220, 220, 220, 0.5)',
                'showgrid': True
            },
            yaxis={
                'title': {
                    'text': 'Temperature (°C)',
                    'font': {'size': 16, 'color': '#1F77B4'}
                },
                'tickfont': {'size': 14, 'color': '#1F77B4'},
                'gridcolor': 'rgba(220, 220, 220, 0.5)',
                'showgrid': True,
                'zeroline': False
            },
            yaxis2={
                'title': {
                    'text': 'Precipitation (mm)',
                    'font': {'size': 16, 'color': '#49AFFF'}
                },
                'tickfont': {'size': 14, 'color': '#49AFFF'},
                'anchor': 'x',
                'overlaying': 'y',
                'side': 'right',
                'showgrid': False,
                'zeroline': False
            },
            legend={
                'orientation': 'h',
                'yanchor': 'bottom',
                'y': 1.02,
                'xanchor': 'center',
                'x': 0.5,
                'font': {'size': 14},
                'bgcolor': 'rgba(255, 255, 255, 0.7)',
                'bordercolor': 'rgba(0, 0, 0, 0.1)',
                'borderwidth': 1
            },
            margin={'l': 40, 'r': 40, 't': 100, 'b': 40},
            hovermode='x unified',
            plot_bgcolor='rgba(240, 248, 255, 0.8)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            height=500,
            shapes=[
                {
                    'type': 'line',
                    'y0': 0, 'y1': 0,
                    'x0': 0, 'x1': 1,
                    'xref': 'paper',
                    'line': {
                        'color': 'rgba(150, 150, 150, 0.5)',
                        'width': 1,
                        'dash': 'dash'
                    }
                }
            ]
        )

        for i, icon in enumerate(weather_icons):
            if i < len(forecast['dates']):
                fig.add_annotation(
                    x=forecast['dates'][i],
                    y=max(forecast['max_temps'][i] + 3, forecast['min_temps'][i] + 12),
                    text=icon,
                    showarrow=False,
                    font=dict(size=24),
                    bgcolor='rgba(255, 255, 255, 0.7)',
                    bordercolor='rgba(0, 0, 0, 0.1)',
                    borderwidth=1,
                    borderpad=4,
                    opacity=0.9
                )

        st_obj.plotly_chart(fig, use_container_width=True)

        st_obj.markdown("""
        <div style='background-color: rgba(240, 248, 255, 0.8); padding: 15px; border-radius: 10px; margin-top: 20px; border-left: 4px solid #3366FF;'>
            <h4 style='margin-top: 0; color: #2C3E50;'>📊 Forecast Legend</h4>
            <p style='margin-bottom: 5px;'><span style='color: #FF5733; font-weight: bold;'>●</span> Red line shows maximum daily temperatures</p>
            <p style='margin-bottom: 5px;'><span style='color: #3366FF; font-weight: bold;'>●</span> Blue line shows minimum daily temperatures</p>
            <p style='margin-bottom: 5px;'><span style='color: #49AFFF; font-weight: bold;'>■</span> Blue bars show expected precipitation</p>
            <p style='margin-bottom: 0;'>Weather icons indicate the predominant weather condition for each day</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st_obj.warning("7-day forecast data is not available.")
    
    st_obj.markdown("</div>", unsafe_allow_html=True)
def fmt_currency(value, currency="MMK"):
    """Formats a numeric value as currency."""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:,.0f} {currency}"

def display_yield_and_profit(st_obj, yield_data: dict, profit_data: dict, area: float):
    """
    Displays the predicted yield and profit.
    """
    if not yield_data and not profit_data:
        st_obj.warning("Yield and profit data is not available.")
        return

    st_obj.markdown('<div class="custom-section">', unsafe_allow_html=True)
    st_obj.markdown('<h3 class="custom-section-title">🌱 Yield & Profit Prediction</h3>', unsafe_allow_html=True)
    
    col1, col2 = st_obj.columns(2)
    
    # Yield info
    yield_per_sqm = yield_data.get('yield_per_sqm')
    total_yield = yield_data.get('total_yield')
    
    # Profit info
    market_price = profit_data.get('market_price')
    predicted_revenue = profit_data.get('total_revenue')

    with col1:
        st_obj.markdown(
            f"""
            <div class="yield-profit-metric">
                <span class="metric-label">Yield per m²</span>
                <span class="metric-value">{fmt(yield_per_sqm, "kg")}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st_obj.markdown(
            f"""
            <div class="yield-profit-metric">
                <span class="metric-label">Total for {fmt(area, "m²")}</span>
                <span class="metric-value">{fmt(total_yield, "kg")}</span>
            </div>
            """,
            unsafe_allow_html=True
        )

    st_obj.markdown('<h3 class="custom-section-title" style="margin-top: 1rem;">💰 Profit Prediction</h3>', unsafe_allow_html=True)
    col3, col4 = st_obj.columns(2)
    with col3:
        st_obj.markdown(
            f"""
            <div class="yield-profit-metric">
                <span class="metric-label">Market Price</span>
                <span class="metric-value">{fmt_currency(market_price)}/kg</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        st_obj.markdown(
            f"""
            <div class="yield-profit-metric">
                <span class="metric-label">Predicted Revenue</span>
                <span class="metric-value">{fmt_currency(predicted_revenue)}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    st_obj.markdown("</div>", unsafe_allow_html=True)

def display_cost_and_roi(st_obj, profit_data: dict):
    """
    Displays the cost breakdown and ROI.
    """
    if not profit_data:
        st_obj.warning("Cost and ROI data is not available.")
        return

    st_obj.markdown('<div class="custom-section">', unsafe_allow_html=True)
    st_obj.markdown('<p class="custom-section-title">💰 Cost & ROI Analysis</p>', unsafe_allow_html=True)

    total_costs = profit_data.get('total_costs', 0)
    total_revenue = profit_data.get('total_revenue', 0)
    estimated_profit = total_revenue - total_costs

    st_obj.markdown(
        f"""
        <div class="yield-profit-grid">
            <div class="yield-profit-metric">
                <span class="metric-label">Total Estimated Cost</span>
                <span class="metric-value">{fmt_currency(total_costs)}</span>
            </div>
            <div class="yield-profit-metric">
                <span class="metric-label">Estimated Profit</span>
                <span class="metric-value">{fmt_currency(estimated_profit)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Detailed cost breakdown
    water_cost = profit_data.get('total_water_cost')
    fertilizer_cost = profit_data.get('total_fertilizer_cost')
    other_costs = profit_data.get('other_costs')

    cost_breakdown_html = f"""
    <div class="cost-breakdown-container">
        <p class="cost-breakdown-title">Detailed Cost Breakdown</p>
        <div class="cost-item">
            <span class="cost-label">💧 Water Cost</span>
            <span class="cost-value">{fmt_currency(water_cost)}</span>
        </div>
        <div class="cost-item">
            <span class="cost-label">🌱 Fertilizer Cost</span>
            <span class="cost-value">{fmt_currency(fertilizer_cost)}</span>
        </div>
        <div class="cost-item">
            <span class="cost-label">⚙️ Other Costs</span>
            <span class="cost-value">{fmt_currency(other_costs)}</span>
        </div>
    </div>
    """
    st_obj.markdown(cost_breakdown_html, unsafe_allow_html=True)

    st_obj.markdown('</div>', unsafe_allow_html=True)
    
def display_main_market_data(st_obj):
    """
    Displays the main market prices table from data/market_prices.csv.
    """
    st_obj.markdown("### 📊 Market Prices (MMK)")
    try:
        # Correct path from project root
        market_prices_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'market_prices.csv')
        df = pd.read_csv(market_prices_path)
        
        # Rename 'S.N' to 'No.' if it exists
        if 'S.N' in df.columns:
            df = df.rename(columns={'S.N': 'No.'})

        st_obj.dataframe(df, hide_index=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st_obj.download_button(
            label="📥 Download Market Prices",
            data=csv,
            file_name='market_prices.csv',
            mime='text/csv',
        )
    except FileNotFoundError:
        st_obj.error("Main market prices file not found. Please ensure 'app/market_prices.csv' exists.")
    except Exception as e:
        st_obj.error(f"An error occurred while loading the main market prices: {e}")

def get_image_as_base64(path):
    """Encodes an image file to a Base64 string for embedding in HTML."""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

def display_ml_recommendations(st_obj, recommendations: list, area_input: str):
    """
    Displays the top 3 crop recommendations using a custom HTML card design
    with yield and profit predictions.
    """
    st_obj.markdown("### 🏆 Top 3 Recommended Crops")
    st_obj.markdown('<div class="crop-cards-grid">', unsafe_allow_html=True)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    def get_card_class(score):
        if score >= 85: return "card-high"
        elif score >= 70: return "card-medium"
        else: return "card-low"

    # Helper to decide progress bar color based on score
    def get_score_color(score: int) -> str:
        """Return a HEX color for the progress bar fill based on the score."""
        if score >= 85:
            return "#4CAF50"  # green
        elif score >= 70:
            return "#FFC107"  # amber
        else:
            return "#F44336"  # red

    trophies = ["🥇", "🥈", "🥉"]

    # --- NEW: Growth Timeline HTML helper ---
    def get_growth_timeline_html(crop_name: str) -> str:
        """Return HTML for the crop growth timeline bar. If no data available, return empty string."""
        stages = CROP_TIMELINES_DATA.get(crop_name.lower(), None)
        if not stages:
            return ""

        total_duration = sum(stage["duration"] for stage in stages if isinstance(stage.get("duration"), (int, float)))
        if total_duration == 0:
            return ""

        # Define a color palette (repeat if more stages than colors)
        palette = [
            "#3498DB",  # blue
            "#2ECC71",  # green
            "#F1C40F",  # yellow
            "#E67E22",  # orange
            "#9B59B6",  # purple
            "#1ABC9C",  # teal
        ]

        bar_segments = []
        label_segments = []
        for idx, stage in enumerate(stages):
            duration = stage.get("duration", 0)
            pct_width = (duration / total_duration) * 100 if total_duration else 0
            color = palette[idx % len(palette)]
            # Rounded corners only for first and last segment
            border_radius_style = "border-top-left-radius:6px; border-bottom-left-radius:6px;" if idx == 0 else ""
            border_radius_style = (
                (border_radius_style + " border-top-right-radius:6px; border-bottom-right-radius:6px;")
                if idx == len(stages) - 1 else border_radius_style
            )
            bar_segments.append(
                f'<div style="width:{pct_width}%; background:{color}; height:14px; display:inline-block; {border_radius_style}"></div>'
            )
            label_segments.append(
                f'<div style="width:{pct_width}%; text-align:center; font-size:11px; line-height:1.2;">{stage["stage"]}<br>{duration}d</div>'
            )

        timeline_html = (
            '<div class="detail-section">'
            '<hr><p class="detail-header">🗓️ Growth Timeline</p>'
            f'<div style="width:100%; margin-bottom:6px;">{"".join(bar_segments)}</div>'
            f'<div style="display:flex; width:100%;">{"".join(label_segments)}</div>'
            '</div>'
        )
        return timeline_html

    for i, crop_rec in enumerate(recommendations):
        score = crop_rec['score']
        card_class = get_card_class(score)
        details = crop_rec['details']
        
        # --- Planting Period Formatting ---
        planting_period = crop_rec.get('planting_season', ['N/A'])
        if isinstance(planting_period, list):
            if len(planting_period) == 2:
                planting_period_str = f"{planting_period[0]} - {planting_period[1]}"
            else:
                planting_period_str = ", ".join(planting_period)
        else:
            planting_period_str = str(planting_period)
        # Wrap in badge for styling
        planting_period_badge = f'<span class="planting-badge">{planting_period_str}</span>'
        
        crop_name_lower = crop_rec["crop_name"].lower()
        image_name = "chilli pepper" if crop_name_lower == "chili pepper" else crop_name_lower
        image_path_jpg = os.path.join(project_root, 'assets', 'images', f'{image_name}.jpg')
        image_path_png = os.path.join(project_root, 'assets', 'images', f'{image_name}.png')
        
        b64_image = get_image_as_base64(image_path_jpg) or get_image_as_base64(image_path_png)
        image_html = f'<img src="data:image/jpeg;base64,{get_image_as_base64(os.path.join(project_root, "assets", "images", "weather.jpg"))}" class="crop-img">'
        if b64_image:
            image_html = f'<img src="data:image/png;base64,{b64_image}" class="crop-img">'

        def create_detail_html(key, header):
            """Return a paragraph element for a detail row with status styling."""
            item = details[key]
            status_class = "detail-success" if item["match"] else "detail-warning"
            icon = "✅" if item["match"] else "⚠️"
            return f'<p class="detail-text {status_class}">{icon} <b>{header}:</b> {item["text"]}</p>'

        farm_details_html = create_detail_html('size', 'Greenhouse Size') + create_detail_html('water', 'Water Availability') + create_detail_html('fertilizer', 'Fertilizer Type')
        weather_details_html = create_detail_html('temperature', 'Temperature') + create_detail_html('humidity', 'Humidity')
        
        # --- NEW: Format profit numbers with commas ---
        price_formatted = f"{crop_rec['market_price_mmk']:,}"
        revenue_formatted = f"{crop_rec['total_revenue_mmk']:,}"
        
        trophy_html = trophies[i] if i < len(trophies) else f"#{i+1}"
        
        score_color = get_score_color(score)
        timeline_section_html = get_growth_timeline_html(crop_rec['crop_name'])
        card_html_top = f"""
        <div class="crop-card-wrapper {card_class}">
            <div class="crop-header"><p class="crop-title">{trophy_html} {crop_rec['crop_name']}</p>{image_html}</div>
            <div class="metric-box">
                <p class="metric-label">Suitability Score</p>
                <p class="metric-value">{score} / 100</p>
                <div class="score-bar"><div class="score-fill" style="width:{score}%; background:{score_color};"></div></div>
            </div>
            <div class="detail-section"><hr><p class="detail-header">🚜 Farm Compatibility</p>{farm_details_html}</div>
            <div class="detail-section"><hr><p class="detail-header">🌦️ Weather Compatibility</p>{weather_details_html}</div>
            <div class="detail-section"><hr><p class="detail-header">📆 Planting Period</p><p class="detail-text">{planting_period_badge}</p></div>
            {timeline_section_html}
            <div class="detail-section">
                <hr><p class="detail-header">🌱 Yield Prediction</p>
                <div class="yield-container">
                    <div class="yield-box"><p class="yield-label">Yield per m²</p><p class="yield-value">{crop_rec['yield_per_sqm_kg']} kg</p></div>
                    <div class="yield-box"><p class="yield-label">Total for {area_input} m²</p><p class="yield-value">{crop_rec['total_yield_kg']} kg</p></div>
                </div>
            </div>
            <div class="detail-section">
                <hr><p class="detail-header">💰 Revenue Prediction</p>
                <div class="yield-container">
                    <div class="yield-box"><p class="yield-label">Market Price</p><p class="yield-value">{price_formatted} MMK/kg</p></div>
                    <div class="yield-box"><p class="yield-label">Predicted Revenue</p><p class="yield-value">{revenue_formatted} MMK</p></div>
                </div>
            </div>
        """
        st_obj.markdown(card_html_top, unsafe_allow_html=True)

        with st_obj.expander(f"Cost & ROI Analysis for {crop_rec['crop_name']}"):
            try:
                area = float(area_input)
                water_available_daily = st.session_state.get('water_liters', None)
                profit_data = predict_profit(
                    crop_name=crop_rec['crop_name'],
                    yield_per_sqm=crop_rec['yield_per_sqm_kg'],
                    total_yield=crop_rec['total_yield_kg'],
                    price_per_kg=crop_rec['market_price_mmk'],
                    greenhouse_size=area,
                    daily_water_available=water_available_daily
                )
                if profit_data:
                    display_cost_and_roi(st_obj, profit_data)
                else:
                    st_obj.warning("Could not calculate Cost & ROI for this crop.")
            except (ValueError, TypeError):
                st_obj.error("Invalid area input for ROI calculation.")
        
        st_obj.markdown("</div>", unsafe_allow_html=True)
    st_obj.markdown('</div>', unsafe_allow_html=True)  # close grid