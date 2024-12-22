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
from src.travily_search import travily_search  # Import the travily_search function
from src.agents.visa_info_agent import fetch_visa_info  # Ensure this import is present
from src.agents.document_management_agent import manage_documents # Import the document management agent

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

def student_info_page():
    st.title("Student Information")
    db = Database()
    table_name = "student_info"

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

    skip_student_info = st.button("Skip Student Info", key="skip_student_info_button") # Added a key
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
        st.session_state.student_data = student_data # Store student data in session state
        st.success("Form Submitted Successfully!")
        st.subheader("Your Information:")
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
            db.clear_table(table_name)
            db.insert_data(table_name, data, StudentInfo)
            st.success("Data Saved to Database!")
        except Exception as e:
            st.error(f"Error saving the data: {e}")
            logging.error(f"Error saving the data: {e}")

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

    if st.button("Activate Visa Checker"):
        st.session_state.current_page = "visa_checker"

    if st.button("Activate Document Checker"):
        st.session_state.current_page = "document_checker"

def visa_checker_page():
    st.title("Visa Requirement Checker")
    selected_country = st.selectbox("Select Destination Country", ["USA", "UK", "Australia"])
    if selected_country:
        visa_info = fetch_visa_info(selected_country)
        print(f"Visa info for {selected_country}: {visa_info}")  # Debug print

        if visa_info:
            st.subheader(f"Visa Information for {selected_country}")
            if 'visa_types' in visa_info:  # Check if 'visa_types' key exists
                for visa_type in visa_info['visa_types']:  # Access 'visa_types' as a dictionary key
                    print(f"Visa Type: {visa_type}")  # Debug print inside the loop
                    st.write(f"**Visa Type:** {visa_type.get('type', 'N/A')}")
                    st.write(f"  - Processing Time: {visa_type.get('processing_time_months', {}).get('range', 'N/A')}")
                    if visa_type.get('financial_requirements'):
                        st.write(f"  - Financial Requirements:")
                        st.write(f"    - Bank Balance (Months): {visa_type['financial_requirements'].get('bank_balance_months', 'N/A')}")
                        if 'estimated_cost_of_attendance_usd' in visa_type['financial_requirements']:
                            st.write(f"    - Estimated Cost of Attendance (USD): {visa_type['financial_requirements']['estimated_cost_of_attendance_usd']}")
                        if 'monthly_living_costs_outside_london_gbp' in visa_type['financial_requirements']:
                            st.write(f"    - Monthly Living Costs (Outside London, GBP): {visa_type['financial_requirements']['monthly_living_costs_outside_london_gbp']}")
                        if 'annual_living_costs_aud' in visa_type['financial_requirements']:
                            st.write(f"    - Annual Living Costs (AUD): {visa_type['financial_requirements']['annual_living_costs_aud']}")
                        st.write(f"    - Proof of Funds Required: {'Yes' if visa_type['financial_requirements'].get('proof_of_funds_required') else 'No'}")
                    if visa_type.get('loan_process'):
                        st.write(f"  - Loan Process:")
                        st.write(f"    - Loan Acceptance Allowed: {'Yes' if visa_type['loan_process'].get('loan_acceptance_allowed') else 'No'}")
                        if visa_type['loan_process'].get('required_documents_summary'):
                            st.write(f"    - Required Documents (Summary):")
                            for doc in visa_type['loan_process']['required_documents_summary']:
                                st.write(f"      - {doc}")
                    if visa_type.get('additional_requirements'):
                        st.write(f"  - Additional Requirements:")
                        for req in visa_type['additional_requirements']:
                            st.write(f"    - {req}")
                    st.write("---")
            else:
                st.warning(f"No visa types information found for {selected_country}.")
        else:
            st.info(f"No specific visa information found for {selected_country} at the moment.")

def document_checker_page():
    st.title("Document Checklist")
    student_data = st.session_state.get('student_data')
    if student_data:
        documents = manage_documents(student_data)
        if documents:
            st.success("Document checklist generated!")
            for doc in documents:
                # Use the document id as a unique key for the checkbox
                checkbox_key = f"doc_checkbox_{doc.id}"
                is_checked = st.checkbox(f"{doc.name} - {doc.description}", key=checkbox_key, value=(doc.status == "Completed"))
                if is_checked:
                    doc.status = "Completed"
                else:
                    doc.status = "Pending"
        else:
            st.error("Failed to generate document checklist.")
    else:
        st.info("Please fill in the Student Information first to generate a personalized document checklist.")

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