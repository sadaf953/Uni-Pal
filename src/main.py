import os
import sys

# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to PYTHONPATH
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from agents.student_info_agent import student_info_page
from config import settings
from models import StudentInfo
from graph_workflow import get_workflow
import logging
from typing import Optional
from agents.visa_info_agent import visa_checker_page
from agents.document_management_agent import document_checker_page
from agents.university_recommendation_agent import scraping_testing_page

settings.LLM_PROVIDER = "groq"
logging.info(f"LLM_PROVIDER set to : {settings.LLM_PROVIDER}")


def main():
    st.set_page_config(layout="wide") # Set layout to wide mode

    if "current_page" not in st.session_state:
        st.session_state.current_page = "student_info"

    with st.sidebar:
        st.title("Navigation")
        if st.button("Student Info"):
            st.session_state.current_page = "student_info"
        if st.button("Scraping & Testing"):
            st.session_state.current_page = "scraping_testing"
        if st.button("Visa Checker"):
            st.session_state.current_page = "visa_checker"
        if st.button("Document Checker"):
            st.session_state.current_page = "document_checker"

    if st.session_state.current_page == "student_info":
        student_info_page()
    elif st.session_state.current_page == "scraping_testing":
        scraping_testing_page()
    elif st.session_state.current_page == "visa_checker":
        visa_checker_page()
    elif st.session_state.current_page == "document_checker":
        document_checker_page()

if __name__ == "__main__":
    if 'next_step' not in st.session_state:
        st.session_state.next_step = False
    if 'workflow_completed' not in st.session_state:
        st.session_state.workflow_completed = False
    if 'table_created' not in st.session_state:
        st.session_state.table_created = False
    if 'skip_student_info' not in st.session_state:
        st.session_state.skip_student_info = False
    if 'raw_results' not in st.session_state:
        st.session_state.raw_results = False
    if  'cleaned_results' not in st.session_state:
        st.session_state.cleaned_results = None
    if 'markdown' not in st.session_state:
        st.session_state.markdown = None
    if 'test_url' not in st.session_state:
        st.session_state.test_url = ''
    if 'student_data' not in st.session_state:
        st.session_state.student_data = None
    main()