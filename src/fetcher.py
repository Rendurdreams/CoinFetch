import os
import json
from datetime import datetime
import requests
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

class CMCDataFetcher:
    def __init__(self):
        self.api_key = os.getenv('CMC_API_KEY')
        if not self.api_key:
            raise ValueError("CMC_API_KEY not found in environment variables")
            
        self.headers = {
            'X-CMC_PRO_API_KEY': self.api_key,
            'Accepts': 'application/json'
        }
        self.base_url = "https://pro-api.coinmarketcap.com/v1"

    def fetch_global_metrics(self):
        """Fetch global cryptocurrency market metrics"""
        endpoint = f"{self.base_url}/global-metrics/quotes/latest"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            data = response.json()
            if data.get('status', {}).get('error_code') != 0:
                raise ValueError(f"API Error: {data.get('status', {}).get('error_message')}")
                
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'data': data['data']
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching global metrics: {e}")
            return None
        except Exception as e:
            print(f"Error processing global metrics: {e}")
            return None

    def fetch_top_100(self):
        """Fetch data for top 100 cryptocurrencies"""
        endpoint = f"{self.base_url}/cryptocurrency/listings/latest"
        params = {
            'limit': 100,
            'convert': 'USD',
            'sort': 'market_cap',
            'sort_dir': 'desc'
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status', {}).get('error_code') != 0:
                raise ValueError(f"API Error: {data.get('status', {}).get('error_message')}")
                
            return {
                'timestamp': datetime.utcnow().isoformat(),
                'data': data['data']
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching top 100: {e}")
            return None
        except Exception as e:
            print(f"Error processing top 100 data: {e}")
            return None

    def save_sample_data(self, data, filename):
        """Save data to a JSON file for inspection"""
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Sample data saved to {filename}")
        except Exception as e:
            print(f"Error saving data to file: {e}")

def main():
    fetcher = CMCDataFetcher()
    
    # Fetch global metrics
    print("\nFetching global metrics...")
    global_metrics = fetcher.fetch_global_metrics()
    if global_metrics:
        print("\nSample global metrics:")
        pprint({
            'total_market_cap': global_metrics['data']['quote']['USD']['total_market_cap'],
            'total_volume_24h': global_metrics['data']['quote']['USD']['total_volume_24h'],
            'btc_dominance': global_metrics['data']['btc_dominance'],
            'eth_dominance': global_metrics['data']['eth_dominance']
        })
        fetcher.save_sample_data(global_metrics, 'sample_global_metrics.json')
    
    # Fetch top 100
    print("\nFetching top 100 cryptocurrencies...")
    top_100 = fetcher.fetch_top_100()
    if top_100:
        print("\nSample of first 3 coins:")
        for coin in top_100['data'][:3]:
            pprint({
                'name': coin['name'],
                'symbol': coin['symbol'],
                'rank': coin['cmc_rank'],
                'price': coin['quote']['USD']['price'],
                'market_cap': coin['quote']['USD']['market_cap']
            })
        fetcher.save_sample_data(top_100, 'sample_top_100.json')

if __name__ == "__main__":
    main()
