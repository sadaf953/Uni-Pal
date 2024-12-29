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

def travily_search_tool():
    """
    Streamlit UI for the Travily search tool.
    """
    st.title("Travily Search Tool")

    search_query = st.text_input("Enter your search query:")
    num_results = st.slider("Number of results:", min_value=1, max_value=10, value=5)

    if st.button("Search"):
        if search_query:
            api_key = settings.TRAVILY_API_KEY
            if api_key:
                with st.spinner("Searching..."):
                    results = travily_search(
                        search_query, api_key, count=num_results
                    )
                    st.session_state.travily_results = results
            else:
                st.error("Travily API key is not configured. Please check your settings.")
        else:
            st.warning("Please enter a search query.")

    if "travily_results" in st.session_state:
        if st.session_state.travily_results:
            st.subheader("Search Results:")
            for url in st.session_state.travily_results:
                st.write(url)
        elif st.button("Search") and search_query:
            st.info("No results found for your query.")

def perform_web_search(state: Dict) -> Dict:
    """
    Perform web search using Tavily for each generated query and return only URLs.

    Args:
        state (Dict): The current state containing search queries

    Returns:
        Dict: Updated state with search results (only URLs)
    """
    queries = state.get("search_queries")
    if not queries:
        raise ValueError("No search queries found in state")

    tavily_api_key = settings.TRAVILY_API_KEY
    if not tavily_api_key:
        raise ValueError("TAVILY_API_KEY not found in settings")

    search_results = {}
    try:
        client = TavilyClient(api_key=tavily_api_key)
        for query in queries:
            response = client.search(query, search_depth="normal")
            urls = [item['url'] for item in response['results']]
            search_results[query] = urls
        state["web_search_results"] = search_results
    except Exception as e:
        raise ValueError(f"Error performing web search: {str(e)}")

    return state