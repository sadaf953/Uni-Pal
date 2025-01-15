# /Users/mahvishsadaf/Desktop/unipal/src/main.py
import os
import sys
import json
from dotenv import load_dotenv
import csv
from src.utils import search_universities, build_query, save_links_to_csv, process_csv
from agents.university_recommendation_agent import scraping_testing_page,process_all_university_links
import pandas as pd
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
from agents.university_recommendation_agent import  recommend_top_universities
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

import streamlit as st
import os

# Assuming your other functions (student_info_page, etc.) are defined

def comprehensive_university_search():
    """
    Comprehensive university search and recommendation workflow.
    Performs all steps from student data to university recommendations.
    """
    st.title("Comprehensive University Search")
    
    # Start with loading student data
    try:
        with open('student_data.json', 'r') as f:
            student_data = json.load(f)
        
        st.subheader("Student Profile")
        st.json(student_data)
    except FileNotFoundError:
        st.error("Student data not found. Please complete student information first.")
        return

    # Build search query based on student data
    try:
        program_field = student_data.get('program_of_interest', 'Computer Science')
        countries = student_data.get('preferred_countries', ['United States'])
        
        query = build_query(program_field, countries)
        st.info(f"Generated Search Query: {query}")
    except Exception as e:
        st.error(f"Error building search query: {e}")
        return

    # Perform university search
    try:
        st.subheader("Searching Universities")
        search_results = search_universities(query)
        
        # Save links to CSV
        output_file = 'processed_universities.csv'
        save_links_to_csv(search_results)
        st.success(f"Found {len(search_results)} universities. Saved to {output_file}")
    except Exception as e:
        st.error(f"Error in university search: {e}")
        return

    # Process CSV to filter and clean links
    try:
        st.subheader("Processing and Filtering Links")
        process_csv('processed_universities.csv', 'filtered_universities.csv')
        st.success("Universities processed and filtered.")
    except Exception as e:
        st.error(f"Error processing universities: {e}")
        return

    # Scrape and extract content from universities
    try:
        st.subheader("Scraping University Websites")
        process_all_university_links()
        st.success("University websites scraped and content extracted.")
    except Exception as e:
        st.error(f"Error scraping universities: {e}")
        return

    # Generate recommendations
    try:
        st.subheader("University Recommendations")
        top_universities = recommend_top_universities()
        
        if not top_universities.empty:
            st.success("Top universities recommended based on your profile!")
        else:
            st.warning("No universities match your profile criteria.")
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return

    st.balloons()
    st.success("Comprehensive university search completed successfully!")

def main():
    st.set_page_config(layout="wide")

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
        if st.button("Generate Recommendations"):
            st.session_state.current_page = "recommendations"

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

            program_field = unique_fields[0]
            countries = unique_countries

            if st.button("Search"):
                if program_field and countries:
                    st.write(f"Searching for top universities in {', '.join(countries)} offering MSc in {program_field}...")
                    results = []
                    links = []
                    global_counter = 1

                    for page in range(3):
                        items, next_page = search_universities(program_field=program_field, countries=countries, start=page * 10 + 1)
                        if not items:
                            break
                        for title, snippet, link in items:
                            results.append((global_counter, title, snippet, link))
                            links.append(link)
                            global_counter += 1
                        if not next_page:
                            break

                    if results:
                        st.session_state.results = results
                        st.session_state.links = links
                        try:
                            save_links_to_csv(links)
                            st.success("Links saved to university.csv successfully!")
                            st.write("### Top Universities and Courses:")
                            st.table(st.session_state.results)
                        except Exception as e:
                            st.error(f"Error saving links: {str(e)}")
                    else:
                        st.warning("No universities found for the given criteria.")
                else:
                    st.error("Please provide program field and countries for search.")

            # Render "Filter Universities" button IF search results exist
            if 'links' in st.session_state and st.session_state.links:
                if st.button("Filter Universities"):
                    st.write("### Started processing")
                    input_file = os.path.join(os.path.dirname(__file__), '..', 'university.csv')
                    output_file = os.path.join(os.path.dirname(__file__), '..', 'processed_universities.csv')

                    if os.path.exists(input_file):
                        placeholder = st.empty()
                        filtered_links = []
                        with st.spinner("Processing links..."):
                            for i, link in enumerate(st.session_state.links):
                                placeholder.write(f"Processing link {i+1}/{len(st.session_state.links)}: {link}")
                                filtered_links.append(link)
                        placeholder.empty()

                        st.write("### Filtered Links:")
                        if filtered_links:
                            for link in filtered_links:
                                st.write(link)
                            st.success("All links processed!")
                            process_csv(input_file, output_file)
                            st.success(f"Processed universities saved to {output_file}")
                            
                            # Process university information right after filtering
                            try:
                                with st.spinner("🔍 Processing detailed university information..."):
                                    process_all_university_links()
                                st.success("✅ Successfully processed university information!")
                                st.session_state.universities_processed = True
                            except Exception as e:
                                st.error(f"❌ Error processing university information: {str(e)}")
                                logging.error(f"Error in process_all_university_links: {str(e)}", exc_info=True)
                        else:
                            st.warning("No links were available to filter.")
                    else:
                        st.error(f"Input file not found")

    elif st.session_state.current_page == "scraping_testing":
        scraping_testing_page()
    elif st.session_state.current_page == "visa_checker":
        visa_checker_page()
    elif st.session_state.current_page == "document_checker":
        document_checker_page()
    elif st.session_state.current_page == "recommendations":
        st.title("🎓 University Recommendations")
        
        # Check if student data exists
        try:
            student_data_path = os.path.join(os.getcwd(), 'student_data.json')
            with open(student_data_path, 'r') as f:
                data = json.load(f)
                if 'students' in data and data['students']:
                    student_data = next(iter(data['students'].values()))
                else:
                    st.error("❌ No student data found. Please complete your profile first.")
                    if st.button("Go to Student Info"):
                        st.session_state.current_page = "student_info"
                    return
        except FileNotFoundError:
            st.error("❌ Please complete your student profile first.")
            if st.button("Go to Student Info"):
                st.session_state.current_page = "student_info"
            return
            
        # Check if universities have been processed
        scraping_dir = os.path.join(os.getcwd(), 'scraping_results')
        if not os.path.exists(scraping_dir) or not os.listdir(scraping_dir):
            st.warning("⚠️ No processed university data found. Please search and filter universities first.")
            if st.button("Go to Student Info"):
                st.session_state.current_page = "student_info"
            return
            
        # Show student profile summary
        st.subheader("📋 Your Profile")
        profile_cols = st.columns(3)
        with profile_cols[0]:
            st.write(f"**Field:** {student_data.get('interested_field_for_masters', 'Not specified')}")
        with profile_cols[1]:
            st.write(f"**Countries:** {', '.join(student_data.get('preferred_countries', ['Not specified']))}")
        with profile_cols[2]:
            st.write(f"**Work Experience:** {student_data.get('work_experience', 'Not specified')}")
            
        # Show academic details
        st.subheader("📚 Academic Details")
        academic_cols = st.columns(4)
        with academic_cols[0]:
            st.write(f"**BTech CGPA:** {student_data.get('btech_cgpa', 'Not specified')}")
        with academic_cols[1]:
            st.write(f"**BTech Branch:** {student_data.get('btech_branch', 'Not specified')}")
        with academic_cols[2]:
            st.write(f"**IELTS:** {student_data.get('ielts_score', 'Not specified')}")
        with academic_cols[3]:
            st.write(f"**TOEFL:** {student_data.get('toefl_score', 'Not specified')}")
            
        # Add button to process universities
        if st.button("🔄 Process Universities", key="process_universities"):
            # Delete and recreate scraping_results folder
            if os.path.exists(scraping_dir):
                import shutil
                shutil.rmtree(scraping_dir)
            os.makedirs(scraping_dir)
            
            # Call the process_all_university_links function
            try:
                process_all_university_links()
                st.success("✅ Successfully processed university information!")
            except Exception as e:
                st.error(f"❌ Error processing universities: {str(e)}")
                logging.error(f"Error in process_all_university_links: {str(e)}", exc_info=True)
            
        # Check if recommendations already exist
        if 'recommendations' in st.session_state:
            st.success("✨ Here are your personalized university recommendations!")
            st.dataframe(st.session_state.recommendations)
            
            # Add refresh button
            if st.button("🔄 Regenerate Recommendations"):
                st.session_state.pop('recommendations', None)
                st.experimental_rerun()
        else:
            st.info("ℹ️ Ready to generate personalized recommendations based on your profile and the processed university data.")
            
            if st.button("🎯 Generate Recommendations", key="gen_recs", use_container_width=True):
                try:
                    with st.spinner("🔍 Analyzing universities and generating recommendations..."):
                        recommendations_df = recommend_top_universities(student_data)
                        
                        if recommendations_df is not None:
                            if not recommendations_df.empty:
                                st.session_state.recommendations = recommendations_df
                                st.success("✨ Recommendations generated successfully!")
                                st.dataframe(recommendations_df)
                            else:
                                st.warning("⚠️ No matching universities found for your profile.")
                        else:
                            st.error("❌ Failed to generate recommendations. Please try again later.")
                except Exception as e:
                    st.error(f"❌ Error generating recommendations: {str(e)}")
                    logging.error(f"Error in recommend_top_universities: {str(e)}", exc_info=True)
                    
                    if "429" in str(e):
                        st.warning("⚠️ API rate limit reached. Please wait a few minutes and try again.")

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
