import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

import requests
from bs4 import BeautifulSoup
from langchain.schema import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import tldextract

from src.config import settings
from src.llm_interface import query_llm


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


# ============================================================================
# Web Scraping Functions
# ============================================================================


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
        response = session.get(website, headers=headers, timeout=40)
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


# ============================================================================
# AI Content Extraction
# ============================================================================

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: {
        "extracted_content": "",
        "error": str(retry_state.outcome.exception())
    }
)
def extract_content_with_ai(html_content: str, user_request: str) -> Dict:
    """
    Extract relevant information from HTML content using AI.
    
    Args:
        html_content (str): Raw HTML content
        user_request (str): User's specific request for information extraction
        
    Returns:
        dict: Extracted information in structured format
    """
    if not html_content:
        return {"extracted_content": "", "error": "No content to analyze"}

    try:
        # Truncate content if too long
        max_chars = 8000
        content = html_content[:max_chars] if len(html_content) > max_chars else html_content
        
        # Create a focused prompt for the AI
        prompt = f"""
        Analyze this webpage content and extract ONLY the following information:
        {user_request}
        
        Content to analyze:
        {content}
        
        Format your response exactly like this:
        1. University Name: [name]
        2. Country: [country]
        3. Tuition Fees: [amount with currency]
        4. Eligibility Criteria: [CGPA, IELTS, TOEFL requirements]
        5. Deadlines: [application deadlines]
        6. Course Curriculum: [brief overview]
        7. Scholarship options: [available scholarships]
        
        If any information is not found, use 'N/A'.
        """
        
        time.sleep(1)  # Rate limiting
        response = query_llm(prompt)
        
        return {
            "extracted_content": response if response else "",
            "source_url": "",
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request
        }
        
    except Exception as e:
        logging.error(f"Error in AI extraction: {str(e)}")
        return {"extracted_content": "", "error": str(e)}


# ============================================================================
# Web Search Functions
# ============================================================================

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


# ============================================================================
# Currency Conversion
# ============================================================================

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


# ============================================================================
# File Operations
# ============================================================================

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