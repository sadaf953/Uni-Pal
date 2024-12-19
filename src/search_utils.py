"""
Search utilities for the university recommendation system.
"""

import os
import json
import logging
from typing import List, Dict, Optional
from dotenv import load_dotenv
from tavily import TavilyClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_api_keys() -> Dict[str, bool]:
    """
    Validate that all required API keys are present.
    """
    load_dotenv()  # Ensure environment variables are loaded
    
    api_keys = {
        'TAVILY_API_KEY': os.getenv('TAVILY_API_KEY'),
        'SERP_API_KEY': os.getenv('SERP_API_KEY'),
    }
    
    validation_results = {}
    for key_name, key_value in api_keys.items():
        is_valid = bool(key_value and len(key_value) > 10)  # Basic validation
        validation_results[key_name] = is_valid
        if not is_valid:
            logger.error(f"Missing or invalid {key_name}")
    
    return validation_results

def perform_tavily_search(query: str, api_key: Optional[str] = None) -> List[Dict]:
    """
    Perform a search using Tavily API with detailed error handling.
    """
    if not api_key:
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    logger.info(f"Performing Tavily search for query: {query}")
    
    try:
        client = TavilyClient(api_key=api_key)
        result = client.search(query, search_depth="advanced")
        
        if not result or 'results' not in result:
            logger.warning(f"No results found for query: {query}")
            return []
        
        formatted_results = []
        for item in result.get('results', []):
            result_item = {
                'title': item.get('title', 'Untitled'),
                'url': item.get('url', ''),
                'content': item.get('content', '')
            }
            formatted_results.append(result_item)
            
        logger.info(f"Found {len(formatted_results)} results for query: {query}")
        return formatted_results
        
    except Exception as e:
        logger.error(f"Error in Tavily search: {str(e)}", exc_info=True)
        raise

def perform_web_search(queries: List[str]) -> Dict[str, List[Dict]]:
    """
    Perform web search for multiple queries with improved error handling.
    """
    # Validate API keys first
    api_validation = validate_api_keys()
    if not api_validation.get('TAVILY_API_KEY'):
        raise ValueError("Invalid or missing TAVILY_API_KEY")
    
    search_results = {}
    total_queries = len(queries)
    
    for i, query in enumerate(queries, 1):
        logger.info(f"Processing query {i}/{total_queries}: {query}")
        try:
            results = perform_tavily_search(query)
            search_results[query] = results
        except Exception as e:
            logger.error(f"Error processing query '{query}': {str(e)}")
            search_results[query] = []  # Empty results for failed query
            
    return search_results
