import os
import json
import logging
from datetime import datetime, timezone
import time
from typing import Dict, Any
from dotenv import load_dotenv
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('AIMarketAnalyzer')

class AIMarketAnalyzer:
    def __init__(self):
        """Initialize the AI Market Analyzer."""
        load_dotenv(override=True)
        
        self.cmc_api_key = os.getenv('CMC_API_KEY')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        
        # Set up API headers
        self.cmc_headers = {
            'X-CMC_PRO_API_KEY': self.cmc_api_key,
            'Accept': 'application/json'
        }
        
        self.openai_headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        logger.info("AI Market Analyzer initialized")

    def fetch_market_data(self) -> Dict[str, Any]:
        """Fetch market data directly from CMC API."""
        try:
            # Fetch global metrics
            global_url = "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest"
            global_response = requests.get(global_url, headers=self.cmc_headers)
            global_data = global_response.json()
            
            # Fetch top 100 coins
            coins_url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
            params = {
                'start': '1',
                'limit': '100',
                'convert': 'USD'
            }
            coins_response = requests.get(coins_url, headers=self.cmc_headers, params=params)
            coins_data = coins_response.json()
            
            market_data = {
                "global_metrics": global_data['data'],
                "top_coins": coins_data['data'][:10]  # Start with top 10 for testing
            }
            
            # Save raw data for inspection
            with open('last_market_data.json', 'w') as f:
                json.dump(market_data, f, indent=2)
            
            logger.info("Market data fetched and saved to last_market_data.json")
            return market_data
            
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}")
            return None

    def analyze_with_ai(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send market data to GPT-4 for analysis."""
        try:
            system_message = """You are a cryptocurrency market analyst expert. Analyze the provided market data and create a comprehensive report with the following sections:

1. Market Overview:
   - Total market cap and 24h change
   - Global market sentiment
   - Key market influences

2. Top Performers Analysis:
   - Best performing assets
   - Notable price movements
   - Volume analysis

3. Risk Analysis:
   - Market volatility assessment
   - Concentration risk
   - Liquidity analysis

4. Key Opportunities:
   - Emerging trends
   - Potential entry points
   - Risk-adjusted opportunities

5. Technical Summary:
   - Key support/resistance levels
   - Volume profiles
   - Market dominance shifts

Format your response as a JSON object with these sections as keys. For each section, include:
- 'summary': A brief overview
- 'key_points': Array of main points
- 'metrics': Relevant numerical data
- 'risks': Any specific risks or concerns
- 'opportunities': Potential opportunities

Keep the analysis concise but data-driven. Include specific numbers and percentages where relevant."""

            # Prepare market data summary
            data_summary = {
                "global_stats": {
                    "total_market_cap": market_data["global_metrics"]["quote"]["USD"]["total_market_cap"],
                    "btc_dominance": market_data["global_metrics"]["btc_dominance"],
                    "eth_dominance": market_data["global_metrics"]["eth_dominance"],
                    "total_volume_24h": market_data["global_metrics"]["quote"]["USD"]["total_volume_24h"]
                },
                "top_coins": [
                    {
                        "name": coin["name"],
                        "symbol": coin["symbol"],
                        "price_usd": coin["quote"]["USD"]["price"],
                        "market_cap": coin["quote"]["USD"]["market_cap"],
                        "volume_24h": coin["quote"]["USD"]["volume_24h"],
                        "percent_change_24h": coin["quote"]["USD"]["percent_change_24h"]
                    }
                    for coin in market_data["top_coins"]
                ]
            }

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=self.openai_headers,
                json={
                    "model": "gpt-4-turbo-preview",
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": f"Please analyze this market data:\n{json.dumps(data_summary, indent=2)}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                analysis = response.json()['choices'][0]['message']['content']
                
                # Save analysis for inspection
                with open('last_analysis.json', 'w') as f:
                    json.dump(json.loads(analysis), f, indent=2)
                
                logger.info("Analysis completed and saved to last_analysis.json")
                return json.loads(analysis)
            else:
                logger.error(f"OpenAI API error: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return None

    def run_single_analysis(self):
        """Run a single analysis cycle for testing."""
        try:
            # Fetch market data
            logger.info("Fetching market data...")
            market_data = self.fetch_market_data()
            if not market_data:
                logger.error("Failed to fetch market data")
                return

            # Get AI analysis
            logger.info("Running AI analysis...")
            analysis = self.analyze_with_ai(market_data)
            if analysis:
                logger.info("Analysis completed successfully")
                logger.info("\nAnalysis Summary:")
                print(json.dumps(analysis, indent=2))
            else:
                logger.error("Analysis failed")
                
        except Exception as e:
            logger.error(f"Error in analysis cycle: {str(e)}")

if __name__ == "__main__":
    analyzer = AIMarketAnalyzer()
    analyzer.run_single_analysis()