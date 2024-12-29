import streamlit as st
from src.config import settings
from typing import List
from tavily import TavilyClient
from typing import List, Dict
import os

def travily_search(search_query: str, api_key: str, count: int = 5) -> List[str]:
    """
    Performs a web search using the Tavily API and returns a list of URLs.

    Args:
        search_query (str): The search query string.
        api_key (str): The Travily API key.
        count (int): The number of results to return.

    Returns:
        List[str]: A list of URLs from the search results.
    """
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(search_query, search_depth="normal")  # Or "advanced" for more details
        urls = [item['url'] for item in response['results'][:count] if 'url' in item]
        return urls
    except Exception as e:
        st.error(f"Error during Tavily search: {e}")
        return []



    if "travily_results" in st.session_state:
        if st.session_state.travily_results:
            st.subheader("Search Results:")
            for url in st.session_state.travily_results:
                st.write(url)
        elif st.button("Search") and search_query:
            st.info("No results found for your query.")
