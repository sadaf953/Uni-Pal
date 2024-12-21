import os
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
import tldextract

from src.config import settings
from src.llm_interface import query_llm
import re


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
        'USD': 82.0,
        'GBP': 103.0,
        'EUR': 89.0,
        'AUD': 54.0,
        'CAD': 60.0,
    }

    try:
        if source_currency not in rates or target_currency != 'INR':
            logging.warning(f"Unsupported currency conversion: {source_currency} to {target_currency}")
            return 0
        return amount * rates[source_currency]
    except Exception as e:
        logging.error(f"Currency conversion error: {str(e)}")
        return 0

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



def extract_json_from_text(text: str) -> List[str]:
    """Extract JSON list from text that might contain markdown or other content."""
    # Try to find JSON array pattern
    json_pattern = r'\[[\s\S]*?\]'
    matches = re.findall(json_pattern, text)
    
    if matches:
        try:
            # Try the last match as it's most likely to be the complete JSON
            return json.loads(matches[-1])
        except json.JSONDecodeError:
            pass
    
    return []

def generate_search_queries(state: Dict) -> Dict:
    """
    Generate search queries based on research topic and additional details.
    Uses Gemini model to generate diverse and relevant search queries.
    """
    config = state.get("config")
    if not config:
        raise ValueError("Research configuration not found in state")

    # Get system and human prompts from Prompts class
    system_prompt = Prompts.generate_search_queries_system_prompt()
    human_message = Prompts.generate_search_queries_human_prompt(
        research_topic=config["research_topic"],
        additional_details=config["additional_details"],
        num_queries=config["num_queries"]
    )

    # Generate queries using Gemini
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = Gemini_Exp1206.invoke(messages)
        content = response.content
        
        # Try to extract JSON from the response
        queries = extract_json_from_text(content)
        
        # Validate and clean queries
        if queries and isinstance(queries, list):
            valid_queries = []
            for query in queries:
                if isinstance(query, str) and query.strip():
                    # Remove any special characters and normalize whitespace
                    cleaned_query = " ".join(query.strip().split())
                    if cleaned_query not in valid_queries:
                        valid_queries.append(cleaned_query)
            
            # Update state with exactly the number of queries requested
            state["search_queries"] = valid_queries[:config["num_queries"]]
        else:
            raise ValueError("Failed to generate valid queries")
            
    except Exception as e:
        raise ValueError(f"Error generating queries: {str(e)}")
    
    return state

def perform_web_search(state: Dict) -> Dict:
    """
    Perform web search using Tavily for each generated query.
    
    Args:
        state (Dict): The current state containing search queries
    
    Returns:
        Dict: Updated state with search results
    """
    queries = state.get("search_queries")
    if not queries:
        raise ValueError("No search queries found in state")

    # Initialize Tavily client
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    
    client = TavilyClient(api_key=tavily_api_key)
    
    # Store results for each query
    search_results = {}
    
    try:
        for query in queries:
            # Perform search with Tavily
            result = client.search(query, search_depth="advanced")
            
            # Extract and format the results
            formatted_results = []
            for item in result.get('results', []):
                result_item = {
                    'title': item.get('title', 'Untitled'),
                    'url': item.get('url', ''),
                    'content': item.get('content', '')
                }
                formatted_results.append(result_item)
            search_results[query] = formatted_results
        
        # Update state with search results
        state["web_search_results"] = search_results
        
    except Exception as e:
        raise ValueError(f"Error performing web search: {str(e)}")
    
    return state

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

def generate_table_of_contents(state: Dict) -> Dict:
    """
    Generate a detailed table of contents based on research configuration and web search results.
    """
    try:
        # Get web search results
        web_results = state.get("web_search_results", {})
        if not web_results:
            raise ValueError("Web search results not found in state")

        # Convert web_results to string format if it's a dictionary
        web_results_str = json.dumps(web_results, indent=2) if isinstance(web_results, dict) else str(web_results)

        # Get prompts
        system_prompt = Prompts.generate_toc_system_prompt()
        human_prompt = Prompts.generate_toc_human_prompt(
            research_topic=state["config"]["research_topic"],
            additional_details=state["config"].get("additional_details", ""),
            format_type=state["config"]["format_type"],
            report_length=state["config"]["report_length"],
            readability_level=state["config"]["readability_level"],
            web_results=web_results_str,
            cleaned_results=state["cleaned_results"]
        )
        
        # Generate ToC using Gemini
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        response = Gemini_Exp1206.invoke(messages)
        toc = response.content
        
        # Store the table of contents in state
        state["table_of_contents"] = toc
        
    except Exception as e:
        raise ValueError(f"Error generating table of contents: {str(e)}")
    
    return state

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


def scrape_and_extract(state: Dict) -> Dict:
    """
    Scrape website content and extract relevant information using AI based on user request.
    
    Args:
        state (Dict): Current state containing website URL and user's extraction request
        
    Returns:
        Dict: Updated state with extracted information
    """
    website_url = state.get("website_url")
    user_request = state.get("extraction_request")
    
    if not website_url or not user_request:
        return {
            **state,
            "error": "Website URL and extraction request are required"
        }
    
    try:
        from scrape import scrape_and_extract as scraper
        
        # Perform scraping and extraction
        extracted_info = scraper(website_url, user_request)
        
        return {
            **state,
            "scraped_data": extracted_info
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Error during scraping: {str(e)}"
        }

def convert_toc_to_json(state: Dict) -> Dict:
    """
    Convert the table of contents into a structured JSON format.
    
    Args:
        state (Dict): Current state containing the table of contents
        
    Returns:
        Dict: Updated state with JSON format of table of contents
    """
    if not hasattr(state, "table_of_contents") or not state.table_of_contents:
        raise ValueError("Table of contents not found in state")
    
    toc_text = state.table_of_contents
    print(f"Converting table of contents:\n{toc_text}")  # Debug print
    
    chapters = []
    current_chapter = None
    current_sections = []
    
    for line in toc_text.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a chapter (starts with "#")
        if line.startswith('# '):
            if current_chapter:
                chapters.append({
                    "chapter": current_chapter,
                    "sections": current_sections
                })
                print(f"Added chapter: {current_chapter} with sections: {current_sections}")  # Debug print
            current_chapter = line.replace('# ', '').strip()
            current_sections = []
            
        # Check if it's a section (starts with "##")
        elif line.startswith('## '):
            section = line.replace('## ', '').strip()
            current_sections.append(section)
            print(f"Added section: {section} to chapter: {current_chapter}")  # Debug print
    
    # Add the last chapter
    if current_chapter:
        chapters.append({
            "chapter": current_chapter,
            "sections": current_sections
        })
        print(f"Added final chapter: {current_chapter} with sections: {current_sections}")  # Debug print
    
    json_output = json.dumps(chapters, indent=2)
    print(f"Final JSON output:\n{json_output}")  # Debug print
    state.toc_json = json_output
    return state

def generate_full_report(state: Dict) -> Dict:
    """
    Generate a complete research report using cleaned data and table of contents.
    
    Args:
        state (Dict): Current state containing cleaned results and table of contents
        
    Returns:
        Dict: Updated state with the final report
    """
    if not hasattr(state, "cleaned_results") or not state.cleaned_results:
        raise ValueError("Cleaned research results not found in state")
    if not hasattr(state, "table_of_contents") or not state.table_of_contents:
        raise ValueError("Table of contents not found in state")
    if not hasattr(state, "config") or not state.config:
        raise ValueError("Research configuration not found in state")

    # Get system and human prompts
    system_prompt = Prompts.generate_report_system_prompt()
    human_message = Prompts.generate_report_human_prompt(
        research_topic=state.config.research_topic,
        cleaned_results=state.cleaned_results,
        table_of_contents=state.table_of_contents,
        report_length=state.config.report_length,
        readability_level=state.config.readability_level
    )

    # Generate report using Gemini
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_message)
    ]
    
    try:
        response = Gemini_Exp1206.invoke(messages)
        report_content = response.content
        
        # Format the final report with table of contents
        final_report = f"""# {state.config.research_topic}

{state.table_of_contents}

{report_content}"""

        state.final_report = final_report
        
    except Exception as e:
        raise ValueError(f"Error generating report: {str(e)}")
    
    return state