import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

def create_price_chart(data, indicators, support_levels=None, resistance_levels=None):
    """
    Create an interactive price chart with technical indicators.
    
    Args:
        data (pandas.DataFrame): Price data
        indicators (dict): Technical indicators data
        support_levels (list): Support levels
        resistance_levels (list): Resistance levels
    
    Returns:
        plotly.graph_objects.Figure: Interactive chart
    """
    if data.empty:
        # Return empty figure if no data
        return go.Figure()
    
    # Create subplots: 2 rows, 1 column, shared x-axis
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.1,
                        row_heights=[0.7, 0.3],
                        subplot_titles=('XAUUSD Price with Indicators', 'RSI(14)'))
    
    # Add candlestick chart to the first subplot
    fig.add_trace(
        go.Candlestick(
            x=data['date'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name='XAUUSD Price'
        ),
        row=1, col=1
    )
    
    # Add Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['bb_upper'],
            line=dict(color='rgba(46, 49, 49, 0.7)', width=1, dash='dash'),
            name='BB Upper'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['bb_middle'],
            line=dict(color='rgba(46, 49, 49, 0.7)', width=1),
            name='BB Middle'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['bb_lower'],
            line=dict(color='rgba(46, 49, 49, 0.7)', width=1, dash='dash'),
            name='BB Lower',
            fill='tonexty',
            fillcolor='rgba(231, 254, 255, 0.2)'
        ),
        row=1, col=1
    )
    
    # Add support and resistance levels if available
    if support_levels is not None and len(support_levels) > 0:
        for level in support_levels:
            fig.add_shape(
                type="line",
                x0=data['date'].iloc[0],
                x1=data['date'].iloc[-1],
                y0=level,
                y1=level,
                line=dict(color="green", width=1, dash="dot"),
                row=1, col=1
            )
    
    if resistance_levels is not None and len(resistance_levels) > 0:
        for level in resistance_levels:
            fig.add_shape(
                type="line",
                x0=data['date'].iloc[0],
                x1=data['date'].iloc[-1],
                y0=level,
                y1=level,
                line=dict(color="red", width=1, dash="dot"),
                row=1, col=1
            )
    
    # Add RSI indicator in the second subplot
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['rsi'],
            line=dict(color='purple', width=1),
            name='RSI(14)'
        ),
        row=2, col=1
    )
    
    # Add RSI overbought/oversold lines
    fig.add_shape(
        type="line",
        x0=data['date'].iloc[0],
        x1=data['date'].iloc[-1],
        y0=70,
        y1=70,
        line=dict(color="red", width=1, dash="dash"),
        row=2, col=1
    )
    
    fig.add_shape(
        type="line",
        x0=data['date'].iloc[0],
        x1=data['date'].iloc[-1],
        y0=30,
        y1=30,
        line=dict(color="green", width=1, dash="dash"),
        row=2, col=1
    )
    
    # Update layout and axes
    fig.update_layout(
        title='XAUUSD Technical Analysis',
        height=800,
        xaxis_rangeslider_visible=False,
        yaxis_title='Price (USD)',
        yaxis2_title='RSI Value',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Set y-axis range for RSI
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    return fig

def create_macd_chart(data):
    """
    Create a MACD chart.
    
    Args:
        data (pandas.DataFrame): Price data with MACD indicators
    
    Returns:
        plotly.graph_objects.Figure: MACD chart
    """
    if data.empty:
        return go.Figure()
    
    fig = go.Figure()
    
    # Add MACD line
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['macd'],
            line=dict(color='blue', width=1),
            name='MACD Line'
        )
    )
    
    # Add Signal line
    fig.add_trace(
        go.Scatter(
            x=data['date'],
            y=data['macd_signal'],
            line=dict(color='red', width=1),
            name='Signal Line'
        )
    )
    
    # Add Histogram as bar chart
    colors = ['green' if val >= 0 else 'red' for val in data['macd_histogram']]
    fig.add_trace(
        go.Bar(
            x=data['date'],
            y=data['macd_histogram'],
            marker_color=colors,
            name='Histogram'
        )
    )
    
    # Update layout
    fig.update_layout(
        title='MACD (12,26,9)',
        height=400,
        yaxis_title='MACD Value',
        xaxis_title='Date',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig
