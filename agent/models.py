from dataclasses import dataclass
from typing import Optional

@dataclass
class CoinData:
    coin: str
    symbol: str
    launch_year: int
    consensus: str
    last_price: Optional[float] = None
    price_timestamp: Optional[str] = None

@dataclass
class AgentResponse:
    answer: str
    source: str  # "Knowledge Base" | "FreeCryptoAPI"
    confidence: float
