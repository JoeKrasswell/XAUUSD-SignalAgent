import streamlit as st
import pandas as pd
import numpy as np
import os
import time
from datetime import datetime

# Import app modules
from market_data import fetch_xauusd_data, get_current_price
from technical_analysis import calculate_all_indicators
from signal_generator import SignalGenerator
from chart_utils import create_price_chart, create_macd_chart

# Set page configuration
st.set_page_config(
    page_title="XAUUSD Trading Signal Agent",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# App title and description
st.title("AI-Powered XAUUSD Trading Signal Agent")
st.markdown("This app analyzes Gold/USD (XAUUSD) price data using technical indicators and generates trading signals with AI.")

# Sidebar
st.sidebar.header("Settings")

# API Key input
st.sidebar.subheader("API Settings")
api_key = st.sidebar.text_input("OpenAI API Key", type="password", help="Enter your OpenAI API key for signal generation. This key is used only for this session and not stored.")

# Data settings
st.sidebar.subheader("Data Settings")
period = st.sidebar.selectbox("Period", ["1d", "2d", "5d", "1mo", "3mo", "6mo", "1y"], index=1)
interval = st.sidebar.selectbox("Interval", ["15m", "30m", "1h", "2h", "4h", "1d"], index=2)

# Technical indicator settings
st.sidebar.subheader("Technical Indicators")
rsi_window = st.sidebar.slider("RSI Window", 7, 21, 14)
macd_fast = st.sidebar.slider("MACD Fast Period", 8, 20, 12)
macd_slow = st.sidebar.slider("MACD Slow Period", 20, 30, 26)
macd_signal = st.sidebar.slider("MACD Signal Period", 5, 15, 9)
bb_window = st.sidebar.slider("Bollinger Bands Window", 10, 30, 20)

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'market_data' not in st.session_state:
    st.session_state.market_data = None
if 'analysis_data' not in st.session_state:
    st.session_state.analysis_data = None
if 'signal_data' not in st.session_state:
    st.session_state.signal_data = None
if 'current_price' not in st.session_state:
    st.session_state.current_price = None

# Function to load data
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_market_data(period, interval):
    data = fetch_xauusd_data(period=period, interval=interval)
    if data.empty:
        st.error("Failed to fetch market data. Please try again later.")
    return data

# Function to update data
def update_data():
    with st.spinner("Fetching market data..."):
        st.session_state.market_data = load_market_data(period, interval)
        
    if not st.session_state.market_data.empty:
        with st.spinner("Calculating technical indicators..."):
            st.session_state.analysis_data = calculate_all_indicators(st.session_state.market_data.copy())
        
        st.session_state.current_price = get_current_price()
        st.session_state.last_update = datetime.now()

# Button to manually update data
if st.sidebar.button("Update Data"):
    update_data()

# Auto-update data if needed
if st.session_state.last_update is None:
    update_data()

# Main content area
if st.session_state.market_data is not None and not st.session_state.market_data.empty:
    # Display current market info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "XAUUSD Price", 
            f"${st.session_state.current_price:.2f}" if st.session_state.current_price else "N/A",
            f"{st.session_state.market_data['percent_change'].iloc[-1]:.2f}%" if not st.session_state.market_data.empty else None
        )
    
    with col2:
        if not st.session_state.market_data.empty and st.session_state.analysis_data:
            current_rsi = st.session_state.analysis_data['data']['rsi'].iloc[-1]
            rsi_color = "🔴" if current_rsi > 70 else "🟢" if current_rsi < 30 else "⚪"
            st.metric("RSI (14)", f"{current_rsi:.2f} {rsi_color}")
    
    with col3:
        last_update_time = st.session_state.last_update.strftime("%H:%M:%S") if st.session_state.last_update else "Never"
        st.write(f"Last Updated: {last_update_time}")
    
    # Display price chart with indicators
    st.subheader("Price Chart with Technical Indicators")
    if st.session_state.analysis_data:
        price_chart = create_price_chart(
            st.session_state.analysis_data['data'],
            st.session_state.analysis_data,
            st.session_state.analysis_data['support_levels'],
            st.session_state.analysis_data['resistance_levels']
        )
        st.plotly_chart(price_chart, use_container_width=True)
    
    # Display MACD chart
    st.subheader("MACD (12,26,9)")
    if st.session_state.analysis_data:
        macd_chart = create_macd_chart(st.session_state.analysis_data['data'])
        st.plotly_chart(macd_chart, use_container_width=True)
    
    # Support and Resistance levels
    st.subheader("Support & Resistance Levels")
    if st.session_state.analysis_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Support Levels**")
            support_levels = st.session_state.analysis_data['support_levels']
            if len(support_levels) > 0:
                for level in sorted(support_levels):
                    st.write(f"${level:.2f}")
            else:
                st.write("No significant support levels identified")
        
        with col2:
            st.write("**Resistance Levels**")
            resistance_levels = st.session_state.analysis_data['resistance_levels']
            if len(resistance_levels) > 0:
                for level in sorted(resistance_levels):
                    st.write(f"${level:.2f}")
            else:
                st.write("No significant resistance levels identified")
    
    # Trading signal section
    st.subheader("AI Trading Signal")
    
    if st.button("Generate Trading Signal"):
        with st.spinner("Analyzing market data and generating trade signal..."):
            # Check for OpenAI API key from user input
            if not api_key:
                st.error("Please enter your OpenAI API key in the sidebar to generate trading signals.")
            else:
                # Generate trading signal with user-provided API key
                signal_generator = SignalGenerator(api_key=api_key)
                st.session_state.signal_data = signal_generator.generate_trade_signal(
                    st.session_state.market_data,
                    st.session_state.analysis_data
                )
    
    # Display trading signal if available
    if st.session_state.signal_data:
        signal_data = st.session_state.signal_data
        
        if "error" in signal_data:
            st.error(signal_data["error"])
        else:
            # Create signal box with appropriate color
            signal_color = "green" if signal_data["signal"] == "BUY" else "red" if signal_data["signal"] == "SELL" else "gray"
            
            st.markdown(
                f"""
                <div style="padding: 20px; border-radius: 10px; background-color: {'rgba(0, 128, 0, 0.1)' if signal_color == 'green' else 'rgba(255, 0, 0, 0.1)' if signal_color == 'red' else 'rgba(128, 128, 128, 0.1)'}">
                    <h3 style="color: {signal_color}; margin: 0;">Signal: {signal_data["signal"]}</h3>
                    <h4>Confidence: {signal_data["confidence"]}</h4>
                    <table>
                        <tr>
                            <td><strong>Entry Price:</strong></td>
                            <td>${signal_data["entry_price"]:.2f}</td>
                        </tr>
                        <tr>
                            <td><strong>Stop Loss:</strong></td>
                            <td>${signal_data["stop_loss"]:.2f}</td>
                        </tr>
                        <tr>
                            <td><strong>Take Profit:</strong></td>
                            <td>${signal_data["take_profit"]:.2f}</td>
                        </tr>
                    </table>
                    <h4>Rationale:</h4>
                    <p>{signal_data["rationale"]}</p>
                    <h4>Risk Factors:</h4>
                    <p>{signal_data["risk_factors"]}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Disclaimer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "**Disclaimer**: This application provides analysis for educational purposes only. "
        "It is not financial advice. Always do your own research before trading."
    )

else:
    st.error("No market data available. Please check your connection and try again.")

# Add footer
st.markdown("---")
st.markdown("Developed with ❤️ using Streamlit, Yahoo Finance, and OpenAI")
