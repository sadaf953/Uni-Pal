import os
import sys
import json

# Get the absolute path of the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to PYTHONPATH
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import streamlit as st
from src.agents.student_info_agent import collect_student_info
from src.database import Database
from src.config import settings
from src.models import StudentInfo
from src.graph_workflow import get_workflow
import logging
from typing import Optional
from src.llm_interface import query_llm
from src.utils import scrape_website, extract_content_with_ai, search_web, clean_search_results
settings.LLM_PROVIDER = "groq" 
logging.info(f"LLM_PROVIDER set to : {settings.LLM_PROVIDER}")


def save_raw_results(data):
    with open('raw_results.json', 'w') as f:
        json.dump(data, f)

def load_raw_results():
    try:
        with open('raw_results.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def main():
    """
    Main function to run the Streamlit application.
    """
    st.title("Student Information Form")

    db = Database()
    table_name = "student_info"

    # Check if table exists, create if it doesn't
    if 'table_created' not in st.session_state:
        try:
            db.connect()
            cursor = db.conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            table_exists = cursor.fetchone()
            if not table_exists:
                columns = StudentInfo.model_fields
                db.create_table(table_name, columns={key: "TEXT" for key in columns})
                logging.info(f"Table {table_name} created.")
            st.session_state.table_created = True
        except Exception as e:
            logging.error(f"Error during table creation: {e}")
            st.error(f"Error during table creation: {e}")
        finally:
            db.close()
    
    skip_student_info = st.button("Skip Student Info")
    if skip_student_info:
      st.session_state.skip_student_info = True


    student_data: Optional[StudentInfo] = None
    if not st.session_state.get("skip_student_info", False):
      student_data = collect_student_info()
    else:
      student_data = StudentInfo(
           name="Test User",
           contact_info="test@example.com",
           marks_10th=90,
           marks_12th=92,
           btech_cgpa=8.5,
           ielts_score=7.0,
           toefl_score=100,
           work_experience="2 years",
           preferred_countries=["USA"],
           btech_branch="Computer Science",
           interested_field_for_masters="Computer Science"
       )


    if student_data:
        st.success("Form Submitted Successfully!")
        st.subheader("Your Information:")
        # Display data in a nice format
        st.write(f"Full Name: {student_data.name}")
        st.write(f"Contact Email/Phone: {student_data.contact_info}")
        st.write(f"10th Grade Marks/Percentage: {student_data.marks_10th}")
        st.write(f"12th Grade Marks/Percentage: {student_data.marks_12th}")
        st.write(f"B.Tech CGPA: {student_data.btech_cgpa}")
        st.write(f"IELTS Score: {student_data.ielts_score if student_data.ielts_score is not None else 'N/A'}")
        st.write(f"TOEFL Score: {student_data.toefl_score if student_data.toefl_score is not None else 'N/A'}")
        st.write(f"Work Experience: {student_data.work_experience if student_data.work_experience else 'N/A'}")
        st.write(f"Preferred Countries: {', '.join(student_data.preferred_countries) if student_data.preferred_countries else 'N/A'}")
        st.write(f"B.Tech Branch: {student_data.btech_branch}")
        st.write(f"Interested Field for Masters: {student_data.interested_field_for_masters if student_data.interested_field_for_masters else 'N/A'}")

        try:
            data = student_data.model_dump()
            # Clear existing data before inserting
            db.clear_table(table_name)
            db.insert_data(table_name, data, StudentInfo)
            st.success("Data Saved to Database!")
        except Exception as e:
            st.error(f"Error saving the data: {e}")
            logging.error(f"Error saving the data: {e}")
        
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
                # Get university recommendations and save the information in universities.csv
                # recommendations = recommend_universities(student_data) 
                logging.info("About to invoke LangGraph workflow")
                workflow = get_workflow()
                result = workflow.invoke({"student_info": student_data}) 
                logging.info("LangGraph workflow invoked successfully")
                st.session_state.workflow_completed = True
                st.write(f"Result from LangGraph {result}") 
            except Exception as e:
                st.error(f"Error running the workflow: {e}")
                logging.error(f"Error running the workflow: {e}")
        if st.session_state.get('workflow_completed', False):
            st.success("Workflow Completed")


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
    main()