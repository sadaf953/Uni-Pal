import os
import csv
import logging
import requests
from dotenv import load_dotenv
from typing import List, Dict
from urllib3.util.retry import Retry
from time import sleep
import datetime
import json
import time 
import logging



# LLM and web scraping imports
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from tavily import TavilyClient

# Local imports
from src.config import settings
from src.llm_interface import query_llm
import streamlit as st

# Load environment variables
load_dotenv()

# API credentials
API_KEY = settings.API_KEY
CX_CODE = settings.CX_CODE

UNWANTED_PATTERNS = ['blogs.lse.ac']
relevant_keywords = ['master', 'ms', 'graduate',]
current_datetime = "some value"

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
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

# def extract_content_with_ai(html_content: str, user_request: str) -> Dict:
#     """
#     Extract relevant information from HTML content using AI.
    
#     Args:
#         html_content (str): Raw HTML content
#         user_request (str): User's specific request for information extraction
        
#     Returns:
#         dict: Extracted information in structured format
#     """
#     if not html_content:
#         return {"extracted_content": "", "error": "No content to analyze"}

#     try:
#         max_chars = 8000
#         content = html_content[:max_chars]
#         prompt = f"""
#         Analyze this webpage content and extract ONLY the following information, return it as a JSON object:
#         {{
#             "university_name" : "[University Name]",
#             "country" : "[Country]",
#             "tuition_fees" : "[Tuition Fees with currency]",
#             "eligibility_criteria" : "[CGPA, IELTS, TOEFL requirements]",
#             "deadlines" : "[application deadlines]",
#             "course_curriculum" : "[brief overview]",
#             "scholarship_options" : "[available scholarships]"
#         }}

#         Content to analyze:
#         {content}

#         If any information is not found, use 'N/A'.
#         """
#         time.sleep(1)  # Rate limiting
#         response = query_ll
# m(prompt)
#         try:
#             return {
#             "extracted_content": json.loads(response) if response else {},
#             "source_url": "",
#             "timestamp": datetime.now().isoformat(),
#             "user_request": user_request
#         }
#         except json.JSONDecodeError as e:
#               logging.error(f"Error decoding json, returning raw content, error is: {e}")
#               return {
#                 "extracted_content": response if response else {},
#                 "source_url": "",
#                 "timestamp": datetime.now().isoformat(),
#                 "user_request": user_request
#             }


#     except Exception as e:
#         logging.error(f"Error in AI extraction: {str(e)}")
#         return {"extracted_content": "", "error": str(e)}


            

# def load_sample_data(file_path: str) -> dict:
#     """
#     Load data from a JSON file.
    
#     Args:
#         file_path (str): Path to the JSON file
        
#     Returns:
#         dict: Loaded JSON data or empty dict if error occurs
#     """
#     try:
#         with open(file_path, 'r') as f:
#             return json.load(f)
#     except Exception as e:
#         logging.error(f"Error loading {file_path}: {str(e)}")
#         return {}



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




# def scrape_website(url: str) -> str:
#     try:
#         response = requests.get(url)
#         soup = BeautifulSoup(response.text, 'html.parser')
#         return soup.get_text()
#     except Exception as e:
#         raise ValueError(f"Error scraping website: {str(e)}")

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
    Extract specific university information from HTML content using AI.
    
    Args:
        html_content (str): Raw HTML content from the website
        user_request (str): User's specific request for information extraction
        
    Returns:
        dict: Structured university information
    """
    try:
        # First clean and extract the main content
        body_content = extract_body_content(html_content)
        clean_content = clean_body_content(body_content)
        
        # Truncate content if too long (Mixtral has token limits)
        max_chars = 25000
        if len(clean_content) > max_chars:
            clean_content = clean_content[:max_chars] + "...[content truncated]"
        
        # Create a structured prompt for the AI
        prompt = f"""
        You are a university data extraction expert. Analyze the following webpage content and extract specific information about the university program.
        
        Webpage content:
        {clean_content}
        
        Extract the following information in a structured format:
        1. University Name: Full name of the university
        2. Program Details:
           - Program Name
           - Department/School
           - Duration
           - Start Dates
        3. Curriculum: Key courses and specializations offered
        4. Admission Requirements:
           - Academic requirements (GPA, degrees)
           - Test scores (GRE, TOEFL, IELTS)
           - Required documents
        5. Application Deadlines:
           - Priority deadline
           - Regular deadline
           - Rolling admissions if applicable
        6. Tuition and Fees:
           - Total program cost
           - Per semester/year breakdown
           - Additional fees
        7. Scholarship Options:
           - Types of scholarships available
           - Eligibility criteria
           - Application process
        8. Contact Information:
           - Department contact
           - Admissions office contact
           - Website/Email

        Format your response as a JSON object with these exact keys. If information is not found, use "Not specified" as the value.
        Be precise and factual. Do not make assumptions or add information not present in the source.
        """
        
        # Add a small delay before making the API call
        time.sleep(2)
        
        # Use configured LLM for extraction
        response = query_llm(prompt)
        
        # Try to parse the response as JSON
        try:
            if isinstance(response, str):
                # Clean up the response string (remove markdown formatting if present)
                response = response.replace('```json', '').replace('```', '').strip()
                content = json.loads(response)
            else:
                content = response
        except json.JSONDecodeError:
            # If JSON parsing fails, structure the response in a basic way
            content = {
                "university_name": "Not specified",
                "program_details": {
                    "name": "Not specified",
                    "department": "Not specified",
                    "duration": "Not specified",
                    "start_dates": "Not specified"
                },
                "curriculum": "Not specified",
                "admission_requirements": {
                    "academic": "Not specified",
                    "test_scores": "Not specified",
                    "documents": "Not specified"
                },
                "deadlines": {
                    "priority": "Not specified",
                    "regular": "Not specified",
                    "rolling": "Not specified"
                },
                "tuition_fees": {
                    "total_cost": "Not specified",
                    "breakdown": "Not specified",
                    "additional_fees": "Not specified"
                },
                "scholarships": {
                    "types": "Not specified",
                    "eligibility": "Not specified",
                    "application": "Not specified"
                },
                "contact_info": {
                    "department": "Not specified",
                    "admissions": "Not specified",
                    "website_email": "Not specified"
                },
                "raw_extraction": response
            }

        return {
            "extracted_content": content,
            "source_url": "",
            "timestamp": datetime.datetime.now().isoformat(),
            "user_request": user_request
        }
    except Exception as e:
        if "429" in str(e) or "Resource has been exhausted" in str(e):
            time.sleep(5)
            raise Exception("API rate limit reached. Please wait a moment before trying again.")
        raise Exception(f"Error during AI extraction: {str(e)}")



def save_links_to_csv(links):
    """
    Saves all university links to a CSV file.
    
    Args:
        links (list): A list of URLs to save.
    """
    try:
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(os.path.abspath('university.csv'))
        os.makedirs(output_dir, exist_ok=True)
        
        # Save links to CSV
        with open('university.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL'])  # Write header
            for link in links:
                writer.writerow([link])
                
        logging.info(f"Successfully saved {len(links)} links to university.csv")
        return True
    except Exception as e:
        logging.error(f"Error saving links to CSV: {str(e)}", exc_info=True)
        raise Exception(f"Failed to save links: {str(e)}")


def search_universities(program_field, countries, start=1):
    """
    Search for universities based on program field and countries.
    
    Args:
        program_field (str): Field of study
        countries (list): List of target countries
        start (int): Starting index for pagination
        
    Returns:
        tuple: (list of results, has next page)
    """
    try:
        # Build the search query
        query = build_query(program_field, countries)
        
        # Make the API request
        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX_CODE}&start={start}"
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        results = response.json()
        
        items = []
        if 'items' in results:
            for item in results['items']:
                title = item.get('title', 'No title available')
                snippet = item.get('snippet', '')
                link = item.get('link', '')
                
                # Check if the link contains any unwanted patterns
                if not any(pattern in link for pattern in UNWANTED_PATTERNS):
                    items.append((title, snippet, link))
        
        next_page = bool(results.get('queries', {}).get('nextPage', []))
        return items, next_page
        
    except Exception as e:
        logging.error(f"Search error: {str(e)}")
        raise Exception(f"Failed to search universities: {str(e)}")


def build_query(program_field, countries):
    base_query = "top universities offering MSC in {} {}"
    queries = [base_query.format(program_field, country) for country in countries]
    return " OR ".join(queries)


def fetch_page_metadata(url):
    """Fetch page title and meta description for classification."""
    try:
        response = requests.get(url, timeout=10)
        
        # Check for non-200 status codes
        if response.status_code != 200:
            return f"Status {response.status_code}", "No description"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else 'No Title'
        description = soup.find('meta', attrs={'name': 'description'})
        description_content = description['content'] if description else 'No Description'
        return title, description_content
    except Exception as e:
        return 'Error', str(e)


def classify_with_llm(title, description, url):
    """Classify the URL using simple heuristics."""
    # Check for program-specific keywords
    program_keywords = ['msc', 'master', 'graduate', 'postgraduate', 'course', 'degree', 'program']
    ai_keywords = ['artificial intelligence', 'ai', 'machine learning', 'data science', 'computer science']
    
    # Convert to lowercase for case-insensitive matching
    title_lower = title.lower()
    description_lower = description.lower()
    url_lower = url.lower()
    
    # Special handling for error cases
    if 'status' in title_lower or 'error' in title_lower:
        return 'Other'
    
    # Check if it's a direct program page
    is_program_page = (
        any(keyword in title_lower for keyword in program_keywords) and
        any(keyword in title_lower or keyword in description_lower for keyword in ai_keywords)
    )
    
    # Check if it's a university homepage
    is_university_homepage = (
        'university' in url_lower or 
        'ac.uk' in url_lower or 
        'edu' in url_lower
    ) and not is_program_page
    
    # Classify
    if is_program_page:
        return 'Direct Program Page'
    elif is_university_homepage:
        return 'University Homepage'
    else:
        return 'Other'


def clean_description(description):
    """Clean up description by removing unnecessary text."""
    # Remove common unnecessary phrases
    unnecessary_phrases = [
        'forbidden', 'no description', 'university homepage', 
        'learn more', 'click here', 'find out more'
    ]
    
    # Convert to lowercase for case-insensitive matching
    cleaned = description.lower()
    
    # Remove unnecessary phrases
    for phrase in unnecessary_phrases:
        cleaned = cleaned.replace(phrase, '').strip()
    
    # Capitalize first letter and return
    return cleaned.capitalize() if cleaned else 'No description'


def process_csv(input_file, output_file):
    """Process URLs from a simple list CSV file."""
    results = []
    with open(input_file, 'r', encoding='utf-8') as infile:
        # Treat each line as a URL directly
        original_urls = set(infile.read().splitlines())
        
    for url in original_urls:
        try:
            # Fetch and classify the URL
            title, description = fetch_page_metadata(url)
            classification = classify_with_llm(title, description, url)
            
            # Clean description
            cleaned_description = clean_description(description)
            
            # Store results, filtering out 'Other' classifications
            if classification != 'Other':
                results.append({
                    'URL': url,
                    'Title': title,
                    'Description': cleaned_description,
                    'Classification': classification
                })
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    # Write results to output CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        if results:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)