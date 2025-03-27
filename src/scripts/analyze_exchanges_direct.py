"""Script to analyze stock exchanges directly from the database."""

from collections import Counter
from src.services.db_service import DatabaseService

def main():
    """Analyze exchanges in the database."""
    db = DatabaseService()
    companies = db.get_all_companies()
    
    # Extract and count exchanges
    exchanges = [company['exchange'] for company in companies if company['exchange']]
    exchange_counts = Counter(exchanges)
    sorted_counts = sorted(exchange_counts.items(), key=lambda x: x[1], reverse=True)
    
    print("\nExchange distribution:")
    for exchange, count in sorted_counts:
        print(f"{exchange}: {count} companies")
    
    print(f"\nTotal unique exchanges: {len(exchange_counts)}")

if __name__ == "__main__":
    main() 