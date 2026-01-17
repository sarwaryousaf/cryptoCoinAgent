from agent.api_client import FreeCryptoAPIClient
from agent.knowledge_base import KnowledgeBase
from agent.models import CoinData
import time

def populate():
    print("Starting Knowledge Base Expansion...")
    api = FreeCryptoAPIClient()
    kb = KnowledgeBase()
    
    # List of top coins to pre-populate
    top_coins = [
        "BTC", "ETH", "BNB", "SOL", "XRP", "USDT", "USDC", "ADA", "DOGE", "AVAX",
        "TRX", "DOT", "LINK", "MATIC", "LTC", "BCH", "UNI", "DAI", "SHIB", "PEPE", "PI"
    ]
    
    count = 0
    for symbol in top_coins:
        print(f"Fetching data for {symbol}...")
        try:
            data = api.fetch_coin_data(symbol)
            if data:
                coin_record = CoinData(
                    coin=data['coin'],
                    symbol=data['symbol'],
                    launch_year=data['launch_year'],
                    consensus=data['consensus'],
                    last_price=data['last_price'],
                    price_timestamp=data['price_timestamp']
                )
                kb.update_coin(coin_record)
                print(f"  -> Added/Updated {data['coin']} (${data['last_price']})")
                count += 1
                # Respect API rate limits
                time.sleep(1.5)
            else:
                print(f"  -> Failed to fetch {symbol}")
        except Exception as e:
            print(f"  -> Error fetching {symbol}: {e}")
            
    print(f"\nExpansion Complete. Added {count} coins to Knowledge Base.")

if __name__ == "__main__":
    populate()
