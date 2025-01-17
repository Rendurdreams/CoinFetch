import os
import json
import logging
from datetime import datetime, timezone
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

# Configure cleaner logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('CMCDataCollector')

# Disable httpx logging
logging.getLogger('httpx').setLevel(logging.WARNING)

class CMCDataCollector:
    GLOBAL_METRICS_TABLE = 'global_metrics'
    COINS_TABLE = 'coins'

    def __init__(self):
        """Initialize the CMC Data Collector."""
        load_dotenv(override=True)
        
        required_env_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'CMC_API_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            raise EnvironmentError(f"Missing environment variables: {', '.join(missing_vars)}")
        
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        self.headers = {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": os.getenv('CMC_API_KEY')
        }
        logger.info("Collector initialized")

    def fetch_global_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch global metrics from CMC API."""
        try:
            response = requests.get(
                "https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch global metrics: {str(e)}")
            return None

    def fetch_top_coins(self, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Fetch top coins from CMC API."""
        try:
            response = requests.get(
                "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest",
                headers=self.headers,
                params={
                    'start': 1,
                    'limit': limit,
                    'convert': 'USD',
                    'sort': 'market_cap',
                    'sort_dir': 'desc'
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data')
        except Exception as e:
            logger.error(f"Failed to fetch top coins: {str(e)}")
            return None

    def process_metrics(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process global metrics data."""
        try:
            raw_data = data['data']
            usd_quote = raw_data['quote']['USD']
            
            return {
                "timestamp": data['status']['timestamp'],
                "btc_dominance": float(raw_data['btc_dominance']),
                "eth_dominance": float(raw_data['eth_dominance']),
                "total_market_cap": float(usd_quote['total_market_cap']),
                "total_volume_24h": float(usd_quote['total_volume_24h']),
                "active_cryptocurrencies": int(raw_data['active_cryptocurrencies']),
                "active_market_pairs": int(raw_data['active_market_pairs']),
                "active_exchanges": int(raw_data['active_exchanges']),
                "defi_volume_24h": float(raw_data['defi_volume_24h']),
                "defi_market_cap": float(raw_data['defi_market_cap']),
                "stablecoin_volume_24h": float(raw_data['stablecoin_volume_24h']),
                "stablecoin_market_cap": float(raw_data['stablecoin_market_cap']),
                "last_updated": raw_data.get('last_updated')
            }
        except Exception as e:
            logger.error(f"Failed to process metrics: {str(e)}")
            return None

    def process_coin_data(self, coins: List[Dict[str, Any]], timestamp: str) -> List[Dict[str, Any]]:
        """Process coins data."""
        processed_coins = []
        
        for coin in coins:
            try:
                quote = coin['quote']['USD']
                processed_coin = {
                    'timestamp': timestamp,
                    'cmc_id': coin['id'],
                    'name': coin['name'],
                    'symbol': coin['symbol'],
                    'slug': coin['slug'],
                    'cmc_rank': coin['cmc_rank'],
                    'circulating_supply': float(coin['circulating_supply'] or 0),
                    'total_supply': float(coin['total_supply'] or 0),
                    'max_supply': float(coin['max_supply'] or 0) if coin['max_supply'] else None,
                    'last_updated': coin['last_updated'],
                    'price_usd': float(quote['price']),
                    'volume_24h': float(quote['volume_24h']),
                    'percent_change_1h': float(quote.get('percent_change_1h') or 0),
                    'percent_change_24h': float(quote.get('percent_change_24h') or 0),
                    'market_cap': float(quote['market_cap']),
                    'market_cap_dominance': float(quote.get('market_cap_dominance') or 0)
                }
                processed_coins.append(processed_coin)
            except Exception as e:
                logger.error(f"Error processing coin {coin.get('name', 'unknown')}")
                continue
                
        return processed_coins

    def store_global_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Store global metrics in database."""
        try:
            self.supabase.table(self.GLOBAL_METRICS_TABLE).insert(metrics).execute()
            logger.info("Global metrics updated")
            return True
        except Exception as e:
            logger.error(f"Failed to store global metrics: {str(e)}")
            return False

    def store_coins(self, coins: List[Dict[str, Any]]) -> bool:
        """Store coins data in database."""
        try:
            if not coins:
                return False
            self.supabase.table(self.COINS_TABLE).insert(coins).execute()
            logger.info(f"Updated data for {len(coins)} coins")
            return True
        except Exception as e:
            logger.error(f"Failed to store coins: {str(e)}")
            return False

    def run(self, interval: int = 300):
        """Run the data collection loop."""
        logger.info(f"Starting data collection (interval: {interval}s)")
        
        while True:
            try:
                current_time = datetime.now(timezone.utc).isoformat()
                
                # Update global metrics
                if metrics_data := self.fetch_global_metrics():
                    if processed_metrics := self.process_metrics(metrics_data):
                        self.store_global_metrics(processed_metrics)
                
                # Update top 100 coins
                if coins_data := self.fetch_top_coins(limit=100):
                    if processed_coins := self.process_coin_data(coins_data, current_time):
                        self.store_coins(processed_coins)
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in collection cycle: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    collector = CMCDataCollector()
    collector.run()