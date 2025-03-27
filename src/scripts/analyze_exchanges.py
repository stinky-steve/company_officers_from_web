"""Script to analyze stock exchanges in the companies file."""

from collections import defaultdict
from pathlib import Path
import csv

from src.services.company_service import CompanyService


def main():
    """Analyze stock exchanges in the companies file."""
    service = CompanyService()
    
    # Count companies by exchange
    exchange_counts = defaultdict(int)
    for company in service.companies:
        if company.exchange:
            exchange_counts[company.exchange] += 1
            
    # Print results
    print("\nStock Exchanges Analysis:")
    print("-" * 40)
    for exchange, count in sorted(exchange_counts.items()):
        print(f"{exchange}: {count} companies")
        
    # Print total
    print("-" * 40)
    print(f"Total companies with exchange info: {sum(exchange_counts.values())}")
    print(f"Total companies without exchange info: {len(service.companies) - sum(exchange_counts.values())}")


if __name__ == "__main__":
    main() 