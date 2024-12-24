import json
import logging
import streamlit as st
from utils import scrape_website, extract_content_with_ai, clean_search_results
from llm_interface import query_llm
from travily_search import travily_search
from config import settings
from graph_workflow import get_workflow

def save_raw_results(data):
    with open('raw_results.json', 'w') as f:
        json.dump(data, f)

def load_raw_results():
    try:
        with open('raw_results.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def scraping_testing_page():
    st.title("Scraping and Searching Tests")

    if st.button("Test LLM"):
        try:
            llm_response = query_llm("Test LLM")
            st.info(f"LLM Response: {llm_response}")
        except Exception as e:
            st.error(f"Error testing LLM: {e}")
            logging.error(f"Error testing LLM: {e}")

    if st.button("Use Predefined URL"):
        st.session_state.test_url = "https://postgraduate.degrees.ed.ac.uk/?id=107%2520&r=site/view&edition=2025"

    test_url = st.text_input("Test Website URL", placeholder="Enter a URL to test", value=st.session_state.get('test_url', ''))

    if st.button("Run All Steps"):
        try:
            st.info("Starting raw data scraping...")
            raw_results = scrape_website(test_url)
            st.success("Raw data scraped successfully.")

            st.info("Saving raw results...")
            st.session_state.raw_results = {
                "web_search_results": {
                    "raw_data": raw_results
                }
            }
            save_raw_results(st.session_state.raw_results)  # Save raw results locally
            st.success("Raw results saved successfully.")

            st.info("Cleaning raw results...")
            cleaned_results = clean_search_results(st.session_state.raw_results)
            st.session_state.cleaned_results = cleaned_results
            st.success("Cleaned results generated successfully.")

            st.info("Extracting content with AI...")
            extracted_content = extract_content_with_ai(cleaned_results['web_search_results']['raw_data'], 'Extract relevant information')
            st.session_state.extracted_content = extracted_content
            st.success("Content extracted successfully.")
            st.write(extracted_content.get('extracted_content', 'No content extracted.'))

        except Exception as e:
            st.error(f"Error in processing: {e}")
            logging.error(f"Error in processing: {e}")

    if st.session_state.get('next_step', False):
        try:
            logging.info("About to invoke LangGraph workflow")
            workflow = get_workflow()
            # Assuming student_data is available in st.session_state from the previous page
            student_data = st.session_state.get('student_data')
            if student_data:
                result = workflow.invoke({"student_info": student_data})
                logging.info("LangGraph workflow invoked successfully")
                st.session_state.workflow_completed = True
                st.write(f"Result from LangGraph {result}")
            else:
                st.warning("Student data not found. Please complete the Student Information page.")
        except Exception as e:
            st.error(f"Error running the workflow: {e}")
            logging.error(f"Error running the workflow: {e}")

    if st.session_state.get('workflow_completed', False):
        st.success("Workflow Completed")

    st.subheader("Get Links based on Input")
    search_input = st.text_input("Enter text to search for relevant links:")
    if st.button("Search Links"):
        if search_input:
            with st.spinner("Searching for links..."):
                api_key = settings.TRAVILY_API_KEY
                if api_key:
                    search_results = travily_search(search_input, api_key)
                    if search_results:
                        st.success("Search complete. Found links:")
                        for link in search_results:
                            st.write(link)
                    else:
                        st.info("No relevant links found.")
                else:
                    st.error("Travily API key is not configured. Please check your settings.")
        else:
            st.warning("Please enter text to search for links.")

   