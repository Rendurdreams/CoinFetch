import os
import requests
from typing import List, Dict
from dotenv import load_dotenv
from supabase import create_client

def setup():
    """Initialize environment and connections."""
    load_dotenv(override=True)
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'CMC_API_KEY']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        exit(1)
    
    return {
        'supabase': create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')),
        'cmc_headers': {
            "Accepts": "application/json",
            "X-CMC_PRO_API_KEY": os.getenv('CMC_API_KEY')
        }
    }

def get_coin_prices(coin_ids: List[int], headers: Dict) -> Dict:
    """Get current prices for coins."""
    try:
        response = requests.get(
            "https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest",
            headers=headers,
            params={
                'id': ','.join(map(str, coin_ids)),
                'convert': 'USD'
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()['data']
    except Exception as e:
        print(f"Error fetching prices: {e}")
        return {}

def search_coin(ticker: str, headers: Dict) -> List[Dict]:
    """Search for coins matching the ticker."""
    try:
        response = requests.get(
            "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map",
            headers=headers,
            params={'symbol': ticker.upper()},
            timeout=30
        )
        response.raise_for_status()
        
        # Filter for active coins only
        coins = [coin for coin in response.json()['data'] if coin['is_active'] == 1]
        
        if coins:
            # Get current prices for all found coins
            prices_data = get_coin_prices([c['id'] for c in coins], headers)
            
            # Enhance coins with price data
            for coin in coins:
                price_info = prices_data.get(str(coin['id']), {}).get('quote', {}).get('USD', {})
                coin['price'] = price_info.get('price', 0)
                coin['market_cap'] = price_info.get('market_cap', 0)
                coin['volume_24h'] = price_info.get('volume_24h', 0)
        
        return coins
    except Exception as e:
        print(f"Error searching for coin: {e}")
        return []

def add_to_tracked(coin: Dict, supabase) -> bool:
    """Add coin to tracked_coins table."""
    try:
        coin_data = {
            'cmc_id': coin['id'],
            'symbol': coin['symbol'],
            'name': coin['name']
        }
        
        supabase.table('tracked_coins').insert(coin_data).execute()
        return True
    except Exception as e:
        print(f"Error adding coin to tracking: {e}")
        return False

def format_number(num: float) -> str:
    """Format numbers for display."""
    if num >= 1_000_000_000:
        return f"${num/1_000_000_000:.2f}B"
    elif num >= 1_000_000:
        return f"${num/1_000_000:.2f}M"
    elif num >= 1:
        return f"${num:.2f}"
    else:
        return f"${num:.8f}"

def main():
    print("Initializing...")
    connections = setup()
    
    while True:
        ticker = input("\nEnter coin ticker (or 'q' to quit): ").strip()
        if ticker.lower() == 'q':
            break
            
        print(f"\nSearching for {ticker}...")
        coins = search_coin(ticker, connections['cmc_headers'])
        
        if not coins:
            print(f"No active coins found matching '{ticker}'")
            continue
        
        # Show coins with detailed info
        if len(coins) > 1:
            print("\nMultiple coins found:")
            print("\n{:<4} {:<20} {:<12} {:<15} {:<15} {:<15} {:<10}".format(
                "Num", "Name", "Symbol", "Price", "Market Cap", "24h Volume", "CMC ID"
            ))
            print("-" * 95)
            
            for i, coin in enumerate(coins, 1):
                print("{:<4} {:<20} {:<12} {:<15} {:<15} {:<15} {:<10}".format(
                    i,
                    coin['name'][:18] + '..' if len(coin['name']) > 18 else coin['name'],
                    coin['symbol'],
                    format_number(coin['price']),
                    format_number(coin['market_cap']),
                    format_number(coin['volume_24h']),
                    coin['id']
                ))
            
            while True:
                try:
                    choice = int(input("\nEnter number of coin to track (0 to skip): "))
                    if choice == 0:
                        break
                    if 1 <= choice <= len(coins):
                        selected_coin = coins[choice - 1]
                        break
                    print("Invalid choice, try again")
                except ValueError:
                    print("Please enter a valid number")
        else:
            selected_coin = coins[0]
            print("\nCoin details:")
            print("-" * 95)
            print(f"Name: {selected_coin['name']}")
            print(f"Symbol: {selected_coin['symbol']}")
            print(f"CMC ID: {selected_coin['id']}")
            print(f"Price: {format_number(selected_coin['price'])}")
            print(f"Market Cap: {format_number(selected_coin['market_cap'])}")
            print(f"24h Volume: {format_number(selected_coin['volume_24h'])}")
            print("-" * 95)
            
            choice = input("Add to tracking? (y/n): ").strip().lower()
            if choice != 'y':
                continue
        
        # Add selected coin to tracking
        if 'selected_coin' in locals():
            if add_to_tracked(selected_coin, connections['supabase']):
                print(f"\nSuccessfully added {selected_coin['name']} to tracking!")
            else:
                print("\nFailed to add coin to tracking")

if __name__ == "__main__":
    try:
        main()
        print("\nGoodbye!")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")