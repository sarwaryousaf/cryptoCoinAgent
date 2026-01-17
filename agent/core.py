import time
from typing import List, Optional, Tuple
from .models import CoinData, AgentResponse
from .knowledge_base import KnowledgeBase
from .api_client import FreeCryptoAPIClient
import re

class ConversationMemory:
    def __init__(self, limit: int = 10):
        self.history: List[str] = [] # Stores user queries for context
        self.last_entity: Optional[str] = None # Last discussed coin symbol
        self.limit = limit

    def add_turn(self, user_query: str):
        self.history.append(user_query)
        if len(self.history) > self.limit:
            self.history.pop(0)

    def set_last_entity(self, symbol: str):
        self.last_entity = symbol
    
    def get_last_entity(self) -> Optional[str]:
        return self.last_entity

class CryptoAgent:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.api = FreeCryptoAPIClient()
        self.memory = ConversationMemory()
        
        # Simple keywords for intent/entity extraction
        # In a real system, use NLP. Here, regex/keywords.
        self.disallowed_keywords = ["predict", "prediction", "forecast", "invest", "buy", "sell", "future"]

    def process_query(self, query: str) -> AgentResponse:
        self.memory.add_turn(query)
        
        # 1. Check Disallowed Queries
        if any(bad in query.lower() for bad in self.disallowed_keywords):
            return self._reject_response("Investment advice and predictions are not allowed.")

        # 2. Extract Entity (Coin)
        entity = self._extract_entity(query)
        if not entity:
            # Check for context (follow-up)
            if self._is_follow_up(query):
                entity = self.memory.get_last_entity()
        
        if not entity:
            return self._reject_response("INSUFFICIENT DATA – Could not identify cryptocurrency.")

        # Resolve entity handling names to symbols if possible via KB first
        # But if it's a new coin, we might have just the symbol or name.
        # Let's standardize on Symbol if found in KB, or assume input is symbol/name.
        
        # 3. Knowledge Base First
        coin_data = self.kb.get_coin(entity)
        source = "Knowledge Base"
        confidence = 1.0
        
        # If found in KB, update context
        if coin_data:
            self.memory.set_last_entity(coin_data.symbol)
            # Check Data Sufficiency & Freshness
            if self._needs_api_update(query, coin_data):
                # Call API
                api_data = self.api.fetch_coin_data(coin_data.symbol)
                if api_data:
                    # Merge/Update KB
                    updated_coin = self._merge_data(coin_data, api_data)
                    self.kb.update_coin(updated_coin)
                    coin_data = updated_coin
                    source = "FreeCryptoAPI" # Updated via API
                else:
                    # API Failed, check if we have enough stale data to answer or reject?
                    # "Data is stale... Used only when Data is missing... or Stale"
                    # If API fails, better to show stale data with warning or reject?
                    # Requirement: "If not in KB and not returned by API -> reject"
                    # It implies if in KB but stale, and API fails, we might still answer BUT source is KB.
                    pass 

        else:
            # Not in KB -> Call API
            api_data = self.api.fetch_coin_data(entity)
            if api_data:
                # Create new record
                coin_data = self._create_coin_from_api(api_data)
                self.kb.update_coin(coin_data)
                self.memory.set_last_entity(coin_data.symbol)
                source = "FreeCryptoAPI"
            else:
                return self._reject_response("INSUFFICIENT DATA – Not found in Knowledge Base or API")

        # 4. Generate Answer
        answer = self._generate_answer(query, coin_data)
        if not answer:
             return self._reject_response("INSUFFICIENT DATA – Data point not available.")
             
        return AgentResponse(
            answer=answer,
            source=source,
            confidence=confidence
        )

    def _extract_entity(self, query: str) -> Optional[str]:
        # 1. Check against KB names/symbols first
        query_words = query.split()
        for word in query_words:
            # Check exact symbol match (case-insensitive)
            clean_word = re.sub(r'[^a-zA-Z]', '', word)
            coin = self.kb.get_coin(clean_word)
            if coin:
                return coin.symbol

        # 2. Pattern Matching for "Price of [X]", "About [X]"
        # Capture the noun after key phrases
        patterns = [
            r"price of\s+([a-zA-Z\s]+)",
            r"value of\s+([a-zA-Z\s]+)",
            r"about\s+([a-zA-Z\s]+)",
            r"tell me about\s+([a-zA-Z\s]+)",
            r"how much is\s+([a-zA-Z\s]+)"
        ]
        
        for p in patterns:
            match = re.search(p, query, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                # If candidate is short, assume symbol. If long, assume name.
                # Remove common stop words if any like "today", "now"
                candidate = re.sub(r'\b(today|now|right now)\b', '', candidate, flags=re.IGNORECASE).strip()
                return candidate.split()[0] # Take first word if multiple, e.g. "Bitcoin Price" -> "Bitcoin"

        # 3. Fallback: Upper case words in original query (potential Tickers)
        # Bitcoin, BTC, SOL, etc. usually capitalized by users or match common tickers
        # Return the first word that looks like a ticker (2-5 letters) or capitalized name
        # Exclude common keywords
        ignored = {"WHO", "WHAT", "WHERE", "WHEN", "WHY", "HOW", "IS", "THE", "A", "AN", "PRICE", "VALUE", "OF"}
        
        for word in query_words:
            clean = re.sub(r'[^a-zA-Z]', '', word)
            if clean.upper() not in ignored and len(clean) >= 2:
                 # If original was capitalized or it looks like a symbol
                 if word[0].isupper() or clean.isupper():
                     return clean

        return None

    def _is_follow_up(self, query: str) -> bool:
        combined = query.lower()
        return "it" in combined or "its" in combined or "this" in combined or "the coin" in combined

    def _needs_api_update(self, query: str, coin: CoinData) -> bool:
        # Check staleness irrespective of query usage if we are using the data.
        # "Stale (older than X minutes)" -> Let's say 2 minutes for "Live" feel
        if not coin.price_timestamp:
            return True
        
        # Check timestamp
        try:
            # flexible parsing
            last_time = time.mktime(time.strptime(coin.price_timestamp, "%Y-%m-%dT%H:%M:%SZ"))
            # If older than 120 seconds (2 mins), update it
            if time.time() - last_time > 120: 
                return True
        except:
            return True
            
        return False

    def _merge_data(self, existing: CoinData, api_data: dict) -> CoinData:
        # Update price fields
        existing.last_price = api_data.get('last_price', existing.last_price)
        existing.price_timestamp = api_data.get('price_timestamp', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        return existing

    def _create_coin_from_api(self, api_data: dict) -> CoinData:
        return CoinData(
            coin=api_data.get('coin', 'Unknown'),
            symbol=api_data.get('symbol', 'UNK'),
            launch_year=api_data.get('launch_year', 0),
            consensus=api_data.get('consensus', 'Unknown'),
            last_price=api_data.get('last_price'),
            price_timestamp=api_data.get('price_timestamp', time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        )

    def _generate_answer(self, query: str, coin: CoinData) -> Optional[str]:
        q = query.lower()
        if "price" in q or "value" in q or "cost" in q:
            if coin.last_price:
                return f"The price of {coin.coin} ({coin.symbol}) is ${coin.last_price}."
            return None
        elif "consensus" in q or "proof" in q:
            if coin.consensus:
                return f"{coin.coin} uses {coin.consensus} consensus."
            return None
        elif "launch" in q or "year" in q or "when" in q:
            if coin.launch_year:
                return f"{coin.coin} was launched in {coin.launch_year}."
            return None
        elif "about" in q or "tell me" in q or "what is" in q:
             # General info
             return f"{coin.coin} ({coin.symbol}) is a cryptocurrency launched in {coin.launch_year} using {coin.consensus}. Current Price: ${coin.last_price}"
        
        # Default fallback context aware
        return f"{coin.coin} ({coin.symbol}): Price ${coin.last_price}, Consensus: {coin.consensus}."

    def _reject_response(self, reason: str) -> AgentResponse:
        return AgentResponse(
            answer=reason,
            source="N/A",
            confidence=0.0
        )
