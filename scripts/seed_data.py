#!/usr/bin/env python
"""
Script to generate sample transaction data for testing.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import random
from datetime import datetime, timedelta
import uuid

import httpx

API_BASE_URL = "http://localhost:8000/api/v1"

MERCHANT_CATEGORIES = [
    "grocery", "restaurant", "gas", "online", "electronics",
    "jewelry", "travel", "entertainment", "retail", "pharmacy"
]

MERCHANT_NAMES = {
    "grocery": ["Walmart", "Target", "Kroger", "Safeway", "Whole Foods"],
    "restaurant": ["McDonald's", "Starbucks", "Chipotle", "Olive Garden", "Subway"],
    "gas": ["Shell", "BP", "Chevron", "ExxonMobil", "Marathon"],
    "online": ["Amazon", "eBay", "PayPal", "Netflix", "Spotify"],
    "electronics": ["Best Buy", "Apple Store", "Samsung", "Newegg", "B&H Photo"],
    "jewelry": ["Tiffany & Co", "Zales", "Kay Jewelers", "Blue Nile", "Brilliant Earth"],
    "travel": ["Expedia", "Booking.com", "Airbnb", "Delta Airlines", "Marriott"],
    "entertainment": ["AMC Theatres", "Barnes & Noble", "GameStop", "Ticketmaster", "Live Nation"],
    "retail": ["Nike", "Adidas", "H&M", "Zara", "Nordstrom"],
    "pharmacy": ["CVS", "Walgreens", "Rite Aid", "Health Mart", "Duane Reade"]
}


def generate_card_number() -> str:
    """Generate a random card number."""
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])


def generate_transaction(is_fraud: bool = False) -> dict:
    """Generate a random transaction."""
    category = random.choice(MERCHANT_CATEGORIES)
    merchant_name = random.choice(MERCHANT_NAMES[category])

    if is_fraud:
        # Fraudulent transactions
        amount = random.choice([
            random.uniform(1000, 10000),  # Large amounts
            random.uniform(0.01, 1),  # Very small amounts
        ])
        hour = random.choice([0, 1, 2, 3, 4, 23])
        location_lat = random.uniform(-90, 90)
        location_lon = random.uniform(-180, 180)
    else:
        # Normal transactions
        amount = random.uniform(5, 500)
        hour = random.randint(6, 22)
        # More realistic location (US centered)
        location_lat = random.uniform(25, 48)
        location_lon = random.uniform(-125, -70)

    # Random time in the last hour
    transaction_time = datetime.utcnow() - timedelta(
        minutes=random.randint(0, 60),
        seconds=random.randint(0, 59)
    )

    return {
        "transaction_id": f"TXN{uuid.uuid4().hex[:8].upper()}",
        "card_number": generate_card_number(),
        "amount": round(amount, 2),
        "currency": "USD",
        "merchant_id": f"M{random.randint(1000, 9999)}",
        "merchant_name": merchant_name,
        "merchant_category": category,
        "location_lat": round(location_lat, 6),
        "location_lon": round(location_lon, 6)
    }


async def create_transaction(client: httpx.AsyncClient, transaction: dict) -> dict:
    """Create a transaction via the API."""
    try:
        response = await client.post(
            f"{API_BASE_URL}/transactions/",
            json=transaction,
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


async def seed_data(num_transactions: int = 100, fraud_rate: float = 0.1):
    """Seed the database with sample transactions."""
    print(f"Seeding {num_transactions} transactions with {fraud_rate*100}% fraud rate...")

    async with httpx.AsyncClient() as client:
        # Check if API is available
        try:
            response = await client.get(f"{API_BASE_URL}/health", timeout=5.0)
            if response.status_code != 200:
                print("API is not healthy. Please start the API server first.")
                return
        except Exception as e:
            print(f"Cannot connect to API: {e}")
            print("Please start the API server first: uvicorn app.main:app --reload")
            return

        # Generate and create transactions
        created_count = 0
        fraud_count = 0

        for i in range(num_transactions):
            is_fraud = random.random() < fraud_rate
            transaction = generate_transaction(is_fraud)

            result = await create_transaction(client, transaction)
            if result:
                created_count += 1
                if result.get("is_fraud"):
                    fraud_count += 1
                    print(f"  [FRAUD] Transaction {transaction['transaction_id']}: ${transaction['amount']:.2f} - Score: {result.get('fraud_score', 0):.4f}")
                else:
                    if (i + 1) % 10 == 0:
                        print(f"  Processed {i + 1}/{num_transactions} transactions...")

        print(f"\nSeeding complete!")
        print(f"Created: {created_count}/{num_transactions} transactions")
        print(f"Fraud detected: {fraud_count}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seed database with sample transactions")
    parser.add_argument("-n", "--num", type=int, default=100, help="Number of transactions")
    parser.add_argument("-f", "--fraud-rate", type=float, default=0.1, help="Fraud rate (0-1)")
    args = parser.parse_args()

    asyncio.run(seed_data(args.num, args.fraud_rate))


if __name__ == "__main__":
    main()
