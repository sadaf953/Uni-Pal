import json
import logging
import time
from datetime import datetime
from typing import List, Dict
from langchain.schema import HumanMessage, SystemMessage
from src.llm_interface import Gemini_Exp1206
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
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

def safe_log(message: str) -> None:
    """
    Logs a message with a timestamp.
    
    Args:
        message (str): The log message to print.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"[{timestamp}] {message}")


def scrape_website(website: str) -> str:
    """
    Scrape website content using requests and BeautifulSoup with robust error handling.
    
    Args:
        website (str): URL of the website to scrape
        
    Returns:
        str: Cleaned text content of the webpage
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

    except (requests.Timeout, requests.RequestException) as e:
        logging.error(f"Error while scraping {website}: {str(e)}")
        return ""
    except Exception as e:
        logging.error(f"Unexpected error while scraping {website}: {str(e)}")
        return ""

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
        max_chars = 8000
        content = html_content[:max_chars]
        prompt = f"""
        Analyze this webpage content and extract ONLY the following information, return it as a JSON object:
        {{
            "university_name" : "[University Name]",
            "country" : "[Country]",
            "tuition_fees" : "[Tuition Fees with currency]",
            "eligibility_criteria" : "[CGPA, IELTS, TOEFL requirements]",
            "deadlines" : "[application deadlines]",
            "course_curriculum" : "[brief overview]",
            "scholarship_options" : "[available scholarships]"
        }}

        Content to analyze:
        {content}

        If any information is not found, use 'N/A'.
        """
        time.sleep(1)  # Rate limiting
        response = query_llm(prompt)
        try:
            return {
            "extracted_content": json.loads(response) if response else {},
            "source_url": "",
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request
        }
        except json.JSONDecodeError as e:
              logging.error(f"Error decoding json, returning raw content, error is: {e}")
              return {
                "extracted_content": response if response else {},
                "source_url": "",
                "timestamp": datetime.now().isoformat(),
                "user_request": user_request
            }


    except Exception as e:
        logging.error(f"Error in AI extraction: {str(e)}")
        return {"extracted_content": "", "error": str(e)}

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




def clean_search_results(state: Dict) -> Dict:
    """
    Convert raw web search results and scraped content into clean markdown format.
    Preserves ALL information with minimal processing.
    """
    try:
        formatted_results = ["## 📚 Web Search Results\n"]
        web_search_results = state.get("web_search_results", {}).get("raw_data", '')
        
        if not web_search_results:
            formatted_results.append("\nNo web search results available.\n")
        else:
            # Process the raw data directly
            formatted_results.append(web_search_results)
        
        # Add scraped website results
        scraped_content = state.get("scraped_content")
        if scraped_content:
            formatted_results.append("\n## 🌐 Analyzed Website Content\n")
            for url, content in scraped_content.items():
                formatted_results.append(f"\n### Analysis of {url}\n")
                formatted_results.append(content)
        
        return {
            **state,
            "cleaned_results": "\n".join(formatted_results)
        }
        
    except Exception as e:
        raise ValueError(f"Error cleaning results: {str(e)}")




def scrape_website(url: str) -> str:
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()
    except Exception as e:
        raise ValueError(f"Error scraping website: {str(e)}")

def extract_body_content(html_content: str) -> str:
    """Extract main content from HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(['script', 'style', 'header', 'footer', 'nav']):
        script.decompose()
    
    # Get text content
    text = soup.get_text(separator='\n', strip=True)
    return text

def clean_body_content(body_content: str) -> str:
    """Clean extracted text content."""
    # Remove extra whitespace and empty lines
    lines = [line.strip() for line in body_content.split('\n')]
    lines = [line for line in lines if line]
    return '\n'.join(lines)



def extract_content_with_ai(html_content: str, user_request: str) -> Dict:
    """
    Extract relevant information from HTML content using AI based on user request.
    Includes retry logic and rate limiting.
    
    Args:
        html_content (str): Raw HTML content from the website
        user_request (str): User's specific request for information extraction
        
    Returns:
        dict: Extracted information in structured format
    """
    try:
        # First clean and extract the main content
        body_content = extract_body_content(html_content)
        clean_content = clean_body_content(body_content)
        
        # Truncate content if too long (Gemini has token limits)
        max_chars = 25000  # Reduced to be more conservative
        if len(clean_content) > max_chars:
            clean_content = clean_content[:max_chars] + "...[content truncated]"
        
        # Create a prompt for the AI
        prompt = f"""
        Analyze the following webpage content and extract information relevant to: {user_request}
        
        Webpage content:
        {clean_content}
        
        Extract and structure the relevant information in a clear format using markdown.
        If no relevant information is found, please indicate that.
        Focus on the most important points and be concise.
        Limit your response to around 1000 words.
        """
        
        # Use Gemini model for extraction with longer timeout
        messages = [
            SystemMessage(content="You are an expert at extracting and structuring relevant information from web content. Be concise and focus on key points."),
            HumanMessage(content=prompt)
        ]
        
        # Add a small delay before making the API call
        time.sleep(3)  # Increased delay between API calls
        
        # Use Gemini model for extraction
        response = Gemini_Exp1206.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "extracted_content": content,
            "source_url": "",
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request
        }
    except Exception as e:
        if "429" in str(e) or "Resource has been exhausted" in str(e):
            time.sleep(5)  # Add extra delay on rate limit
            raise Exception("API rate limit reached. Please wait a moment before trying again.")
        raise Exception(f"Error during AI extraction: {str(e)}")



