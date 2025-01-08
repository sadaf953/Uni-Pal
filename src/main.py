# /Users/mahvishsadaf/Desktop/unipal/src/main.py
import os
import sys
import json
from dotenv import load_dotenv
import csv

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

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
from src.json_storage import JsonStorage
from src.utils import search_universities,save_links_to_csv,build_query, process_csv


settings.LLM_PROVIDER = "groq"
logging.info(f"LLM_PROVIDER set to : {settings.LLM_PROVIDER}")
# Import API_KEY and CX_CODE from settings
API_KEY = settings.API_KEY
CX_CODE = settings.CX_CODE



def get_unique_fields_and_countries():
    """
    Extract unique program fields and countries from student_data.json.
    
    Returns:
        tuple: A tuple containing (unique_fields, unique_countries)
    """
    try:
        with open(os.path.join(os.path.dirname(__file__), '..', 'student_data.json'), 'r') as f:
            data = json.load(f)
        
        # Extract unique fields and countries
        unique_fields = set()
        unique_countries = set()
        
        for student in data.get('students', {}).values():
            field = student.get('interested_field_for_masters', '')
            countries = student.get('preferred_countries', [])
            
            if field:
                unique_fields.add(field)
            unique_countries.update(countries)
        
        # Default fallback if no data found
        unique_fields = unique_fields or {'Artificial Intelligence', 'Computer Science'}
        unique_countries = unique_countries or {'USA', 'UK', 'Australia'}
        
        return list(unique_fields), list(unique_countries)
    
    except Exception as e:
        logging.error(f"Error reading student data: {e}")
        # Fallback to default values
        return ['Artificial Intelligence'], ['USA', 'UK', 'Australia']

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
        if st.session_state.get('student_data'):
            student_data = st.session_state['student_data']
            country = student_data.get('preferred_countries')
            course = student_data.get('interested_field_for_masters')

            if country and course:
                if isinstance(country, list) and country:
                    country_for_search = country[0]

            unique_fields, unique_countries = get_unique_fields_and_countries()
            
            program_field =unique_fields[0]  
            countries =unique_countries

            if st.button("Search") and program_field and countries:
                query = build_query(program_field, countries)
                st.write(f"Searching for top universities in {', '.join(countries)} offering MSC in {program_field}...")
                results = []
                links = []
                global_counter = 1
                
                # Pagination loop (3 pages, 30 results max)
                for page in range(3):
                    items, next_page = search_universities(query, start=page * 10 + 1)
                    if not items:
                        break
                    for title, snippet, link in items:
                        results.append((global_counter, title, snippet, link))
                        links.append(link)  # Collect links for CSV
                        global_counter += 1
                    if not next_page:
                        break
                
                # Save the links to the CSV file
                if links:
                    save_links_to_csv(links)
                    st.success("Links saved to university.csv successfully!")
                
                # Display results in a table (only university names and course snippets)
                if results:
                    st.write("### Top Universities and Courses:")
                    data = []
                    for number, title, snippet, link in results:
                        data.append([title, snippet, link])
                    st.table(data)
                else:
                    st.error("No results found!")                             

    elif st.session_state.current_page == "scraping_testing":
        st.subheader("University Links Processing")
        
        input_file = os.path.join(os.path.dirname(__file__), '..', 'university.csv')
        output_file = os.path.join(os.path.dirname(__file__), '..', 'processed_universities.csv')
        
        st.write("Click the button below to process university links:")
        if st.button("Filter Universities"):
            if os.path.exists(input_file):
                with st.spinner("Processing links..."):
                    process_csv(input_file, output_file)
                st.success(f"Processed universities saved to {output_file}")
            else:
                st.error(f"Input file {input_file} not found")
        
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
