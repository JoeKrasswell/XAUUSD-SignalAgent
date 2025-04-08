import pandas as pd
import numpy as np
from scipy.signal import find_peaks

def calculate_rsi(data, window=14):
    """
    Calculate the Relative Strength Index (RSI).
    
    Args:
        data (pandas.DataFrame): DataFrame with price data
        window (int): Period for RSI calculation (default: 14)
    
    Returns:
        pandas.Series: RSI values
    """
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    # Handle division by zero
    rs = avg_gain / avg_loss.replace(0, np.finfo(float).eps)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate Moving Average Convergence Divergence (MACD).
    
    Args:
        data (pandas.DataFrame): DataFrame with price data
        fast_period (int): Fast EMA period
        slow_period (int): Slow EMA period
        signal_period (int): Signal line period
    
    Returns:
        tuple: (MACD line, Signal line, Histogram)
    """
    ema_fast = data['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = data['close'].ewm(span=slow_period, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data, window=20, num_std=2):
    """
    Calculate Bollinger Bands.
    
    Args:
        data (pandas.DataFrame): DataFrame with price data
        window (int): Window for moving average
        num_std (int): Number of standard deviations
    
    Returns:
        tuple: (Upper band, Middle band, Lower band)
    """
    middle_band = data['close'].rolling(window=window).mean()
    std_dev = data['close'].rolling(window=window).std()
    
    upper_band = middle_band + (std_dev * num_std)
    lower_band = middle_band - (std_dev * num_std)
    
    return upper_band, middle_band, lower_band

def find_support_resistance(data, window=10, prominence=0.5):
    """
    Find support and resistance levels based on local minima and maxima.
    
    Args:
        data (pandas.DataFrame): DataFrame with price data
        window (int): Window for peaks detection
        prominence (float): Prominence factor for peak detection
    
    Returns:
        tuple: (Support levels, Resistance levels)
    """
    # Identify peaks and troughs in the price data
    prices = data['close'].values
    
    # Find peaks for resistance levels
    resistance_idx, _ = find_peaks(prices, distance=window, prominence=prominence)
    resistance_levels = prices[resistance_idx]
    
    # Find troughs for support levels
    support_idx, _ = find_peaks(-prices, distance=window, prominence=prominence)
    support_levels = prices[support_idx]
    
    # Focus on only the most recent levels (last 3-5)
    support_levels = np.array(sorted(support_levels))[-5:] if len(support_levels) > 0 else []
    resistance_levels = np.array(sorted(resistance_levels))[-5:] if len(resistance_levels) > 0 else []
    
    # Remove duplicate or very close levels (within 0.1% of each other)
    if len(support_levels) > 0:
        support_levels = np.array([support_levels[0]] + [s for i, s in enumerate(support_levels[1:]) 
                                  if abs(s - support_levels[i]) / s > 0.001])
    
    if len(resistance_levels) > 0:
        resistance_levels = np.array([resistance_levels[0]] + [r for i, r in enumerate(resistance_levels[1:]) 
                                     if abs(r - resistance_levels[i]) / r > 0.001])
    
    return support_levels, resistance_levels

def calculate_all_indicators(data):
    """
    Calculate all technical indicators.
    
    Args:
        data (pandas.DataFrame): DataFrame with price data
    
    Returns:
        dict: Dictionary containing all calculated indicators
    """
    # Calculate RSI
    data['rsi'] = calculate_rsi(data)
    
    # Calculate MACD
    macd_line, signal_line, histogram = calculate_macd(data)
    data['macd'] = macd_line
    data['macd_signal'] = signal_line
    data['macd_histogram'] = histogram
    
    # Calculate Bollinger Bands
    upper_band, middle_band, lower_band = calculate_bollinger_bands(data)
    data['bb_upper'] = upper_band
    data['bb_middle'] = middle_band
    data['bb_lower'] = lower_band
    
    # Find support and resistance levels
    support_levels, resistance_levels = find_support_resistance(data)
    
    return {
        'data': data,
        'support_levels': support_levels,
        'resistance_levels': resistance_levels,
        'last_price': data['close'].iloc[-1] if not data.empty else None
    }
