import os
import json
from openai import OpenAI

class SignalGenerator:
    def __init__(self, api_key=None):
        """
        Initialize the SignalGenerator with OpenAI API
        
        Args:
            api_key (str, optional): OpenAI API key provided by the user.
                If not provided, attempt to get from environment variables.
        """
        # Get API key from parameter or environment variables
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
            
        self.client = OpenAI(api_key=api_key)
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        
    def generate_trade_signal(self, market_data, analysis_data):
        """
        Generate trade signals based on technical analysis using OpenAI.
        
        Args:
            market_data (pandas.DataFrame): The market price data
            analysis_data (dict): Dictionary containing technical indicators
        
        Returns:
            dict: Trade signal containing entry, stop-loss, take-profit and explanation
        """
        try:
            if market_data.empty or not analysis_data:
                return {
                    "error": "Insufficient data to generate trade signal"
                }
            
            # Extract the most recent data points for the prompt
            recent_data = market_data.tail(24).copy()  # Last 24 hours
            
            # Prepare market data summary
            market_summary = {
                "current_price": analysis_data['last_price'],
                "price_change_24h": recent_data['close'].iloc[-1] - recent_data['close'].iloc[0],
                "price_change_pct_24h": ((recent_data['close'].iloc[-1] / recent_data['close'].iloc[0]) - 1) * 100,
                "high_24h": recent_data['high'].max(),
                "low_24h": recent_data['low'].min(),
                "volatility_24h": recent_data['high'].max() - recent_data['low'].min(),
                "current_rsi": analysis_data['data']['rsi'].iloc[-1],
                "current_macd": analysis_data['data']['macd'].iloc[-1],
                "current_macd_signal": analysis_data['data']['macd_signal'].iloc[-1],
                "current_bb_upper": analysis_data['data']['bb_upper'].iloc[-1],
                "current_bb_lower": analysis_data['data']['bb_lower'].iloc[-1],
                "support_levels": list(analysis_data['support_levels']),
                "resistance_levels": list(analysis_data['resistance_levels']),
            }
            
            # Format technical indicator trends
            rsi_trend = "overbought" if market_summary["current_rsi"] > 70 else "oversold" if market_summary["current_rsi"] < 30 else "neutral"
            macd_trend = "bullish" if market_summary["current_macd"] > market_summary["current_macd_signal"] else "bearish"
            bb_position = "upper_band" if analysis_data['last_price'] > market_summary["current_bb_upper"] else \
                          "lower_band" if analysis_data['last_price'] < market_summary["current_bb_lower"] else "middle"
            
            # Prepare the market data part of the prompt
            market_data_prompt = f"""
You are an expert gold trading analyst specialized in XAUUSD technical analysis.
Analyze the following market data and generate a trading signal based only on the provided information.

Current Market Conditions for XAUUSD (Gold/USD):
- Current Price: ${market_summary['current_price']:.2f}
- 24h Price Change: ${market_summary['price_change_24h']:.2f} ({market_summary['price_change_pct_24h']:.2f}%)
- 24h High: ${market_summary['high_24h']:.2f}
- 24h Low: ${market_summary['low_24h']:.2f}
- 24h Volatility: ${market_summary['volatility_24h']:.2f}

Technical Indicators:
- RSI (14): {market_summary['current_rsi']:.2f} ({rsi_trend})
- MACD: {market_summary['current_macd']:.2f} (Signal: {market_summary['current_macd_signal']:.2f}, Trend: {macd_trend})
- Bollinger Bands: Price is near the {bb_position} (Upper: ${market_summary['current_bb_upper']:.2f}, Lower: ${market_summary['current_bb_lower']:.2f})

Support and Resistance Levels:
- Support Levels: {[f"${level:.2f}" for level in market_summary['support_levels']]}
- Resistance Levels: {[f"${level:.2f}" for level in market_summary['resistance_levels']]}
"""

            # Schema part as a plain string, not f-string
            schema_prompt = """
Based on this technical analysis, provide a trading recommendation in JSON format:
1. Signal type (BUY, SELL, or NEUTRAL)
2. Entry price
3. Stop-loss price (specify a technically appropriate level)
4. Take-profit price (specify a technically appropriate level)
5. Confidence level (LOW, MEDIUM, HIGH)
6. Short explanation of the trade rationale
7. Key risk factors to monitor

Response must be in a single valid JSON object with these exact keys:
{
  "signal": "BUY, SELL, or NEUTRAL",  
  "entry_price": 0.0,
  "stop_loss": 0.0,
  "take_profit": 0.0,
  "confidence": "LOW, MEDIUM, or HIGH",
  "rationale": "explanation here",
  "risk_factors": "risks here"
}
"""
            # Combine the parts
            prompt = market_data_prompt + schema_prompt

            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the response
            response_content = response.choices[0].message.content
            signal_data = json.loads(response_content)
            
            return signal_data
            
        except Exception as e:
            print(f"Error generating trade signal: {e}")
            return {
                "signal": "ERROR",
                "entry_price": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0,
                "confidence": "LOW",
                "rationale": f"Failed to generate trade signal: {str(e)}",
                "risk_factors": "Unable to assess risks due to signal generation failure"
            }
