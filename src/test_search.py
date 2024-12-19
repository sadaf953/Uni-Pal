"""
Test script for search functionality.
"""

import logging
from search_utils import validate_api_keys, perform_web_search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_search():
    """
    Test the search functionality.
    """
    # First, validate API keys
    logger.info("Validating API keys...")
    api_validation = validate_api_keys()
    
    for key_name, is_valid in api_validation.items():
        logger.info(f"{key_name}: {'Valid' if is_valid else 'Invalid or Missing'}")
    
    if not api_validation.get('TAVILY_API_KEY'):
        logger.error("Cannot proceed with test: Missing Tavily API key")
        return
    
    # Test queries
    test_queries = [
        "top computer science universities in USA",
        "scholarship opportunities for international students"
    ]
    
    logger.info(f"Testing search with {len(test_queries)} queries...")
    
    try:
        results = perform_web_search(test_queries)
        
        # Log results summary
        for query, query_results in results.items():
            logger.info(f"\nResults for query: {query}")
            logger.info(f"Number of results: {len(query_results)}")
            
            if query_results:
                # Show first result as example
                first_result = query_results[0]
                logger.info("First result example:")
                logger.info(f"Title: {first_result.get('title')}")
                logger.info(f"URL: {first_result.get('url')}")
                logger.info(f"Content length: {len(first_result.get('content', ''))}")
            else:
                logger.warning("No results found for this query")
                
    except Exception as e:
        logger.error(f"Error during test: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_search()
