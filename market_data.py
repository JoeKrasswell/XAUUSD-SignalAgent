import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def fetch_xauusd_data(period='2d', interval='1h'):
    """
    Fetch XAUUSD (Gold/USD) price data from Yahoo Finance.
    
    Args:
        period (str): Period to fetch data for (e.g., '2d' for 2 days, '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        interval (str): Data interval (e.g., '1h' for hourly data, '15m', '30m', '60m', '1d')
    
    Returns:
        pandas.DataFrame: Historical price data
    """
    try:
        # Yahoo Finance ticker for Gold/USD
        ticker = "GC=F"
        
        # Validate period parameter - convert to valid Yahoo Finance format
        valid_periods = ['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max']
        
        # Map some common alternative formats to valid ones
        period_map = {
            '1w': '5d',      # Map 1 week to 5 days
            '1m': '1mo',     # Map 1 month to 1mo
            '3m': '3mo',     # Map 3 months to 3mo
            '6m': '6mo',     # Map 6 months to 6mo
            '1yr': '1y',     # Map 1 year to 1y
            '2yr': '2y',     # Map 2 years to 2y
            '5yr': '5y',     # Map 5 years to 5y
            '10yr': '10y'    # Map 10 years to 10y
        }
        
        # Convert period to a valid format if needed
        if period in period_map:
            period = period_map[period]
        elif period not in valid_periods:
            print(f"Warning: Invalid period '{period}', falling back to '1d'")
            period = '1d'  # Default to 1 day if invalid
            
        # Fetch the data
        data = yf.download(ticker, period=period, interval=interval)
        
        # Print debug information
        print(f"Downloaded data shape: {data.shape}")
        print(f"Column names: {list(data.columns)}")
        
        if data.empty:
            raise ValueError("No data retrieved from Yahoo Finance")
        
        # Handle multi-level columns if present
        if isinstance(data.columns, pd.MultiIndex):
            print("Multi-level columns detected, flattening...")
            # Take the first level if it has names like 'Open', 'Close', etc.
            if all(col[0] in ['Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'] for col in data.columns):
                data.columns = [col[0] for col in data.columns]
            else:
                # Fallback: flatten the multi-index to strings
                data.columns = [f"{col[0]}_{col[1]}" if len(col) > 1 else col[0] for col in data.columns]
            print(f"After flattening columns: {list(data.columns)}")
        
        # First, reset the index to make the datetime accessible as a column
        data = data.reset_index()
        print(f"After reset_index, columns: {list(data.columns)}")
        
        # Now lowercase column names
        data.columns = [str(col).lower().replace(' ', '_') for col in data.columns]
        print(f"After lowercase, columns: {list(data.columns)}")
        
        # Ensure datetime format is consistent
        date_col = None
        if 'date' in data.columns:
            date_col = 'date'
        elif 'datetime' in data.columns:
            date_col = 'datetime'
            data = data.rename(columns={'datetime': 'date'})
        else:
            # Find any column that might contain date/time information
            for col in data.columns:
                if any(time_word in str(col).lower() for time_word in ['date', 'time', 'datetime']):
                    date_col = col
                    data = data.rename(columns={col: 'date'})
                    break
        
        # If we found a date column, ensure it's in datetime format
        if date_col:
            data['date'] = pd.to_datetime(data['date'])
        else:
            print("No date column found in data!")
            # This is a critical error, but try to recover
            # If there's an index that might be datetime, convert it
            if isinstance(data.index, pd.DatetimeIndex):
                data['date'] = data.index
            else:
                raise ValueError("Could not identify a datetime column in the data")
        
        # Make sure we have all necessary price columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        actual_columns = list(data.columns)
        
        # Try to match column names like 'open', 'high', etc. first by direct match
        for req_col in required_columns:
            if req_col not in actual_columns:
                # Try case-insensitive match
                for col in actual_columns:
                    if req_col == str(col).lower():
                        data = data.rename(columns={col: req_col})
                        print(f"Renamed {col} to {req_col}")
                        break
        
        # Check which columns we still need to find
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"Still missing required columns: {missing_columns}")
            
            # Try to find columns containing the required name
            for req_col in list(missing_columns):  # Use a copy for iteration since we modify it
                potential_matches = []
                for col in data.columns:
                    if req_col in str(col).lower():
                        potential_matches.append(col)
                
                if potential_matches:
                    # Use the first matching column
                    matching_col = potential_matches[0]
                    data = data.rename(columns={matching_col: req_col})
                    print(f"Matched {matching_col} to {req_col}")
                    missing_columns.remove(req_col)
        
        # If we still have missing columns, we can't proceed
        if missing_columns:
            # Last attempt: try to use columns with similar financial meanings
            # For example, if 'close' is missing but 'adj_close' exists
            if 'close' in missing_columns and 'adj_close' in data.columns:
                data = data.rename(columns={'adj_close': 'close'})
                missing_columns.remove('close')
                print("Using 'adj_close' for 'close'")
            
            # If still missing columns, raise error
            if missing_columns:
                raise ValueError(f"Could not find required columns: {missing_columns}")
        
        # Add a simple price change column
        data['price_change'] = data['close'].diff()
        data['percent_change'] = data['close'].pct_change() * 100
        
        print(f"Final data shape: {data.shape}, columns: {list(data.columns)}")
        return data
    
    except Exception as e:
        print(f"Error fetching XAUUSD data: {e}")
        import traceback
        traceback.print_exc()
        # Return an empty DataFrame with expected columns if there's an error
        return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])

def get_current_price():
    """
    Get the latest XAUUSD price.
    
    Returns:
        float: Current price of XAUUSD
    """
    try:
        data = yf.download("GC=F", period="1d", interval="1m")
        
        # Debug information
        print(f"Current price data shape: {data.shape}")
        print(f"Current price columns: {list(data.columns)}")
        
        # Handle multi-level columns if present
        if isinstance(data.columns, pd.MultiIndex):
            print("Multi-level columns detected in current price data, flattening...")
            # Take the first level if it has names like 'Open', 'Close', etc.
            if any('Close' in col for col in data.columns):
                # Find the column containing 'Close'
                close_cols = [col for col in data.columns if 'Close' in col]
                print(f"Found close columns: {close_cols}")
                close_col = close_cols[0]
                current_price = data[close_col].iloc[-1]
                print(f"Using column {close_col}, value: {current_price}")
                return current_price
            
            # Otherwise, flatten and continue with normal processing
            data.columns = [f"{col[0]}_{col[1]}" if len(col) > 1 else col[0] for col in data.columns]
            print(f"After flattening, columns: {list(data.columns)}")
        
        # Handle potential case sensitivity issues
        if 'Close' in data.columns:
            current_price = data['Close'].iloc[-1]
            print(f"Found 'Close' column, value: {current_price}")
        elif 'close' in data.columns:
            current_price = data['close'].iloc[-1]
            print(f"Found 'close' column, value: {current_price}")
        else:
            # Try to find a column name that might be 'close'
            close_cols = [col for col in data.columns if 'close' in str(col).lower()]
            print(f"Potential close columns: {close_cols}")
            
            if close_cols:
                close_col = close_cols[0]
                current_price = data[close_col].iloc[-1]
                print(f"Using column '{close_col}', value: {current_price}")
            else:
                # Look for columns containing 'close' in any part of the name
                close_cols = [col for col in data.columns if any('close' in part.lower() for part in str(col).split('_'))]
                if close_cols:
                    close_col = close_cols[0]
                    current_price = data[close_col].iloc[-1]
                    print(f"Using column with close in name: '{close_col}', value: {current_price}")
                else:
                    # Last resort: try to use any numeric column's last value
                    numeric_cols = [col for col in data.columns if pd.api.types.is_numeric_dtype(data[col])]
                    if numeric_cols:
                        close_col = numeric_cols[0]
                        current_price = data[close_col].iloc[-1]
                        print(f"Using numeric column '{close_col}', value: {current_price}")
                    else:
                        raise ValueError("Could not find any suitable column for price data")
        
        return current_price
    except Exception as e:
        print(f"Error fetching current price: {e}")
        import traceback
        traceback.print_exc()
        return None
