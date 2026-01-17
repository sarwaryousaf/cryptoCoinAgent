import json
import os
from typing import Optional, List
from .models import CoinData

class KnowledgeBase:
    def __init__(self, data_path: str = "data/kb.json"):
        self.data_path = data_path
        self._data: List[CoinData] = []
        self._load_kb()

    def _load_kb(self):
        if not os.path.exists(self.data_path):
            self._data = []
            return

        try:
            with open(self.data_path, 'r') as f:
                raw_data = json.load(f)
                self._data = [CoinData(**item) for item in raw_data]
        except Exception as e:
            print(f"Error loading KB: {e}")
            self._data = []

    def save_kb(self):
        try:
            # Convert objects back to dicts
            raw_data = [
                {
                    "coin": item.coin,
                    "symbol": item.symbol,
                    "launch_year": item.launch_year,
                    "consensus": item.consensus,
                    "last_price": item.last_price,
                    "price_timestamp": item.price_timestamp
                }
                for item in self._data
            ]
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
            
            with open(self.data_path, 'w') as f:
                json.dump(raw_data, f, indent=4)
        except Exception as e:
            print(f"Error saving KB: {e}")

    def get_coin(self, query: str) -> Optional[CoinData]:
        """
        Search for a coin by symbol or name (case-insensitive).
        """
        query = query.lower().strip()
        for coin in self._data:
            if coin.symbol.lower() == query or coin.coin.lower() == query:
                return coin
        return None

    def update_coin(self, coin_data: CoinData):
        """
        Update existing coin or add new one.
        """
        existing = self.get_coin(coin_data.symbol)
        if existing:
            # Update fields
            existing.last_price = coin_data.last_price
            existing.price_timestamp = coin_data.price_timestamp
            # Update other static fields if needed, but usually static facts don't change often
            existing.consensus = coin_data.consensus
            existing.launch_year = coin_data.launch_year
        else:
            self._data.append(coin_data)
        
        self.save_kb()
