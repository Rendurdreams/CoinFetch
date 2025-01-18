import os
import logging
from datetime import datetime, timezone
import time
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
import requests
from supabase import create_client, Client

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('TrackedCoinsCollector')
logging.getLogger('httpx').setLevel(logging.WARNING)

class TrackedCoinsCollector:
    COINS_TABLE = 'coins'
    TRACKED_COINS_TABLE = 'tracked_coins'

    def __init__(self):
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
        logger.info("Tracked Coins Collector initialized")

    def fetch_tracked_coins(self) -> List[int]:
        """Fetch list of tracked coin IDs."""
        try:
            # First, let's see what's in the tracked_coins table
            response = self.supabase.table(self.TRACKED_COINS_TABLE)\
                .select('*')\
                .execute()
            
            if not response.data:
                logger.warning("No coins found in tracked_coins table")
                return []

            # Log each tracked coin
            for coin in response.data:
                logger.info(f"Found tracked coin: {coin.get('symbol', 'Unknown')} (ID: {coin.get('cmc_id', 'Unknown')})")

            tracked_ids = [int(item['cmc_id']) for item in response.data]
            logger.info(f"Total tracked coins found: {len(tracked_ids)}")
            return tracked_ids

        except Exception as e:
            logger.error(f"Failed to fetch tracked coins: {str(e)}")
            return []

    def fetch_coin_data(self, cmc_ids: List[int]) -> Optional[List[Dict[str, Any]]]:
        """Fetch data for tracked coins."""
        if not cmc_ids:
            logger.warning("No coin IDs provided to fetch_coin_data")
            return None
        
        try:
            logger.info(f"Fetching data for coins: {cmc_ids}")
            response = requests.get(
                "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest",
                headers=self.headers,
                params={
                    'id': ','.join(map(str, cmc_ids)),
                    'convert': 'USD'
                },
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            # Log the raw response for debugging
            logger.debug(f"Raw API response: {data}")
            
            coins = [data['data'][str(id)] for id in cmc_ids if str(id) in data['data']]
            logger.info(f"Successfully fetched data for {len(coins)} coins")
            return coins

        except Exception as e:
            logger.error(f"Failed to fetch coin data: {str(e)}")
            if 'response' in locals():
                try:
                    logger.error(f"API Response: {response.text}")
                except:
                    pass
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
                    'cmc_rank': coin.get('cmc_rank', 0),
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
                logger.info(f"Processed coin {coin['symbol']} (ID: {coin['id']}) - Price: ${quote['price']}")
            except Exception as e:
                logger.error(f"Error processing coin {coin.get('name', 'unknown')}: {str(e)}")
                continue
                
        return processed_coins

    def store_coins(self, coins: List[Dict[str, Any]]) -> bool:
        """Store coins data in database."""
        try:
            if not coins:
                logger.warning("No coins to store")
                return False
                
            # Log what we're about to store
            for coin in coins:
                logger.info(f"Storing data for {coin['symbol']} (ID: {coin['cmc_id']}) - Price: ${coin['price_usd']}")
            
            response = self.supabase.table(self.COINS_TABLE).insert(coins).execute()
            
            # Log the response
            logger.info(f"Supabase response: {response}")
            logger.info(f"Successfully stored data for {len(coins)} tracked coins")
            return True

        except Exception as e:
            logger.error(f"Failed to store coins: {str(e)}")
            return False

    def run(self, interval: int = 300):
        """Run the tracked coins collection loop."""
        logger.info(f"Starting tracked coins collection (interval: {interval}s)")
        
        while True:
            try:
                current_time = datetime.now(timezone.utc).isoformat()
                logger.info(f"Starting collection cycle at {current_time}")
                
                # Fetch and update tracked coins
                tracked_ids = self.fetch_tracked_coins()
                if not tracked_ids:
                    logger.warning("No tracked coins found, waiting for next cycle")
                    time.sleep(interval)
                    continue
                
                logger.info(f"Found {len(tracked_ids)} coins to track")
                coins_data = self.fetch_coin_data(tracked_ids)
                
                if coins_data:
                    processed_coins = self.process_coin_data(coins_data, current_time)
                    if processed_coins:
                        self.store_coins(processed_coins)
                    else:
                        logger.warning("No coins were processed successfully")
                else:
                    logger.warning("Failed to fetch coin data")
                
                logger.info(f"Cycle complete, waiting {interval} seconds")
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in collection cycle: {str(e)}")
                time.sleep(60)

if __name__ == "__main__":
    collector = TrackedCoinsCollector()
    collector.run()