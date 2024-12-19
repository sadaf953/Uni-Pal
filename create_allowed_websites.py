import json
import requests
from src.config import settings
import os
import logging
from typing import List, Dict

def search_web(query: str) -> List[Dict[str, str]]:
    """
    Searches the web using the Google Search API and returns a list of results.

    Args:
        query: The search query.

    Returns:
        A list of dictionaries, each containing the 'title' and 'link' of a search result.
    """
    serp_api_key = settings.SERP_API_KEY
    if not serp_api_key:
        logging.error("SERP_API_KEY not found in environment variables")
        return []
    
    url = "https://serpapi.com/search"
    params = {
      "engine": "google",
      "q": query,
      "api_key": serp_api_key,
      "num": 10,
      "timeout": 15
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        results = response.json()
        search_results = []
        if "organic_results" in results:
          for result in results["organic_results"]:
            search_results.append({
              "title": result.get("title"),
              "link": result.get("link"),
            })
        logging.info(f"Successfully searched for: {query}")
        return search_results
    except requests.exceptions.RequestException as e:
        logging.error(f"Error searching for {query}: {e}")
        return []
    except Exception as e:
        logging.error(f"General error in search {query}: {e}")
        return []


def create_allowed_websites_file():
    """Creates a data/allowed_websites.json file with a list of relevant universities."""
    queries = [
        "top universities in the USA for computer science",
        "top universities in the UK for computer science",
        "top universities in Australia for computer science",
        "list of universities in USA",
        "list of universities in UK",
        "list of universities in Australia"
    ]

    all_links = set()
    for query in queries:
        search_results = search_web(query)
        if search_results:
            for result in search_results:
                link = result.get("link")
                if link:
                    all_links.add(link)

    allowed_domains = set()
    for link in all_links:
      parts = link.split("/")
      if len(parts) > 2:
        domain = parts[2]
        allowed_domains.add(domain)


    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    if not os.path.exists(data_dir):
       os.makedirs(data_dir)
    file_path = os.path.join(data_dir, 'allowed_websites.json')
    
    with open(file_path, 'w') as f:
      json.dump({"allowed_domains": list(allowed_domains)}, f, indent=2)
    print(f"Created {file_path}")

if __name__ == '__main__':
    create_allowed_websites_file()