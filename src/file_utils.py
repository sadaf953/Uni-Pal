"""
File operation utilities for the university recommendation system.
"""

# Standard library imports
import os
import json
import logging
from typing import List


def load_sample_data(file_path: str) -> dict:
    """
    Load data from a JSON file.
    
    Args:
        file_path (str): Path to the JSON file
        
    Returns:
        dict: Loaded JSON data or empty dict if error occurs
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading {file_path}: {str(e)}")
        return {}


def load_allowed_domains() -> List[str]:
    """
    Load allowed domains from configuration.
    
    Returns:
        List[str]: List of allowed domain names
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'allowed_websites.json')
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data.get("allowed_domains", [])
    except Exception as e:
        logging.error(f"Error loading allowed domains: {str(e)}")
        return []
