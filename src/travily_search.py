import streamlit as st
import requests
from src.config import settings
from src.utils import safe_log
from typing import List

def travily_search(search_query: str, api_key: str, count: int = 5) -> List[str]:
    """
    Performs a web search using the Travily API and returns a list of URLs.

    Args:
        search_query (str): The search query string.
        api_key (str): The Travily API key.
        count (int): The number of results to return.

    Returns:
        List[str]: A list of URLs from the search results.
    """
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": search_query, "count": count}
    try:
        response = requests.post("https://api.travily.ai/search", headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        safe_log(f"Travily API Response: {data}")  # Log the raw response for debugging
        urls = [result.get("link") for result in data.get("organic", []) if result.get("link")]
        return urls
    except requests.exceptions.HTTPError as http_err:
        safe_log(f"HTTP error during Travily search: {http_err}")
        st.error(f"HTTP error during search: {http_err}")
        return []
    except requests.exceptions.ConnectionError as conn_err:
        safe_log(f"Connection error during Travily search: {conn_err}")
        st.error(f"Connection error during search. Please check your internet connection.")
        return []
    except requests.exceptions.Timeout as timeout_err:
        safe_log(f"Timeout error during Travily search: {timeout_err}")
        st.error("Search timed out. Please try again later.")
        return []
    except requests.exceptions.RequestException as e:
        safe_log(f"Error during Travily search: {e}")
        st.error(f"Error during search: {e}")
        return []
    except ValueError as e:  # Catch JSONDecodeError which is a subclass of ValueError
        safe_log(f"Error parsing Travily response: Invalid JSON - {e}")
        st.error(f"Error processing search results: The API returned an unexpected format.")
        return []
    except Exception as e:
        safe_log(f"Unexpected error processing Travily response: {e}")
        st.error(f"An unexpected error occurred while processing search results: {e}")
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
                    st.session_state.travily_results = travily_search(
                        search_query, api_key, count=num_results
                    )
            else:
                st.error("Travily API key is not configured. Please check your settings.")
        else:
            st.warning("Please enter a search query.")

    if "travily_results" in st.session_state:
        if st.session_state.travily_results:
            st.subheader("Search Results:")
            for url in st.session_state.travily_results:
                st.write(url)
        elif st.button("Search") and search_query:  # Display message only after a search attempt with a query
            st.info("No results found for your query.")