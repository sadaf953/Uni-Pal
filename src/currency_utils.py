"""
Currency conversion utilities for the university recommendation system.
"""

# Standard library imports
import logging


def convert_currency(amount: float, source_currency: str, target_currency: str) -> float:
    """
    Convert currency with predefined rates.
    
    Args:
        amount (float): Amount to convert
        source_currency (str): Source currency code
        target_currency (str): Target currency code
        
    Returns:
        float: Converted amount
    """
    rates = {
        'USD': 82.0,   # 1 USD = 82 INR
        'GBP': 103.0,  # 1 GBP = 103 INR
        'EUR': 89.0,   # 1 EUR = 89 INR
        'AUD': 54.0,   # 1 AUD = 54 INR
        'CAD': 60.0,   # 1 CAD = 60 INR
    }
    
    try:
        if source_currency not in rates or target_currency != 'INR':
            logging.warning(f"Unsupported currency conversion: {source_currency} to {target_currency}")
            return 0
        return amount * rates[source_currency]
    except Exception as e:
        logging.error(f"Currency conversion error: {str(e)}")
        return 0
