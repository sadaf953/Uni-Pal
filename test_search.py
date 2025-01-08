from src.utils import build_query, search_universities, classify_university_link, save_links_to_csv
from src.config import settings
from dotenv import load_dotenv
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

def test_university_search():
    # Test parameters
    program_field = "Computer Science"
    countries = ["USA", "UK", "Canada"]
    
    # Build search query
    query = build_query(program_field, countries)
    logging.info(f"Search query: {query}")
    
    # Verify API credentials
    logging.info(f"API Key exists: {bool(settings.API_KEY)}")
    logging.info(f"CX Code exists: {bool(settings.CX_CODE)}")
    
    try:
        # Search for universities
        results, next_page = search_universities(query)
        logging.info(f"Found {len(results)} initial results")
        
        if not results:
            logging.warning("No results found. Checking API response directly...")
            url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={settings.API_KEY}&cx={settings.CX_CODE}&start=1"
            response = requests.get(url)
            logging.info(f"API Response Status: {response.status_code}")
            logging.info(f"API Response: {response.json()}")
            return
        
        # Extract links
        links = [link for _, _, link in results]
        logging.info(f"Extracted {len(links)} links")
        
        # Save to CSV
        save_links_to_csv(links)
        logging.info("Saved results to university.csv")
        
    except Exception as e:
        logging.error(f"Error during search: {e}")

if __name__ == "__main__":
    test_university_search()
