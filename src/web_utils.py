"""
Web scraping and search utilities for the university recommendation system.
"""

# Standard library imports
import logging
import time
from typing import List, Dict, Optional

# Third-party imports
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tldextract

# Local imports
from src.config import settings


def setup_requests_session() -> requests.Session:
    """
    Set up a requests session with retry logic.
    
    Returns:
        requests.Session: Configured session with retry strategy
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def scrape_website(website: str) -> str:
    """
    Scrape website content using requests and BeautifulSoup with robust error handling.
    
    Args:
        website (str): URL of the website to scrape
        
    Returns:
        str: HTML content of the webpage
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                     '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    session = setup_requests_session()

    try:
        response = session.get(website, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'iframe', 'nav', 'footer']):
            element.decompose()
            
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        return main_content.get_text(separator='\n', strip=True) if main_content else ""
        
    except requests.Timeout:
        logging.error(f"Timeout while scraping {website}")
        return ""
    except requests.RequestException as e:
        logging.error(f"Request error while scraping {website}: {str(e)}")
        return ""
    except Exception as e:
        logging.error(f"Unexpected error while scraping {website}: {str(e)}")
        return ""


def search_web(query: str) -> List[Dict[str, str]]:
    """
    Search the web using Google Search API with domain filtering.
    
    Args:
        query (str): Search query string
        
    Returns:
        List[Dict[str, str]]: List of search results with titles and links
    """
    serp_api_key = settings.SERP_API_KEY
    if not serp_api_key:
        logging.error("SERP_API_KEY not found")
        return []
    
    try:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "api_key": serp_api_key,
            "num": 5,
            "timeout": 15
        }
        
        session = setup_requests_session()
        response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        results = response.json()
        
        search_results = []
        if "organic_results" in results:
            allowed_domains = load_allowed_domains()
            for result in results["organic_results"]:
                if is_allowed_domain(result.get('link', ''), allowed_domains):
                    search_results.append({
                        "title": result.get("title", ""),
                        "link": result.get("link", "")
                    })
        
        return search_results
        
    except requests.RequestException as e:
        logging.error(f"Search API error: {str(e)}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error in search: {str(e)}")
        return []


def is_allowed_domain(url: str, allowed_domains: List[str]) -> bool:
    """
    Check if a URL's domain is in the allowed list.
    
    Args:
        url (str): URL to check
        allowed_domains (List[str]): List of allowed domains
        
    Returns:
        bool: True if domain is allowed, False otherwise
    """
    try:
        extracted = tldextract.extract(url)
        domain = f"{extracted.domain}.{extracted.suffix}"
        return domain in allowed_domains
    except Exception:
        return False
