from agent.core import CryptoAgent
import time

def run_tests():
    print("Initializing Agent...")
    agent = CryptoAgent()
    
    # Test 1: Known Coin (Bitcoin)
    print("\n--- Test 1: Known Coin (Bitcoin) ---")
    response = agent.process_query("Tell me about Bitcoin")
    print(f"Query: 'Tell me about Bitcoin'")
    print(f"Answer: {response.answer}")
    
    # Since we enabled aggressive auto-update, source might be API if data is stale.
    # Bitcoin generic data is in KB, but if timestamp is old, it fetches.
    # Let's just check we get an answer.
    print(f"Source: {response.source}")
    assert response.answer is not None

    # Test 2: Follow-up
    print("\n--- Test 2: Follow-up (Context) ---")
    response = agent.process_query("What is its consensus?")
    print(f"Query: 'What is its consensus?'")
    print(f"Answer: {response.answer}")
    assert "Bitcoin" in response.answer or "Proof of Work" in response.answer

    # Test 3: Disallowed
    print("\n--- Test 3: Disallowed Query ---")
    response = agent.process_query("Predict the price of Bitcoin next week")
    print(f"Query: 'Predict the price...'")
    print(f"Answer: {response.answer}")
    assert response.answer == "Investment advice and predictions are not allowed."

    # Test 4: Unknown Coin (Solana) - From Mock DB/API
    print("\n--- Test 4: Unknown Coin (Solana) ---")
    response = agent.process_query("Price of Solana")
    print(f"Query: 'Price of Solana'")
    print(f"Answer: {response.answer}")
    print(f"Source: {response.source}")
    assert response.source == "FreeCryptoAPI"

    # Test 5: New Random Coin (XRP) - Dynamic Simulation/API
    print("\n--- Test 5: New Random Coin (XRP) ---")
    response = agent.process_query("What is the price of XRP?")
    print(f"Query: 'What is the price of XRP?'")
    print(f"Answer: {response.answer}")
    print(f"Source: {response.source}")
    assert "XRP" in response.answer
    assert response.source == "FreeCryptoAPI"

if __name__ == "__main__":
    run_tests()
