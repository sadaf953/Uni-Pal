import streamlit as st
from src.models import StudentInfo
import logging
import re
from typing import Dict
from src.database import Database


def is_valid_email(email: str) -> bool:
    """
    Checks if the given string is a valid email format.
    """
    email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_regex, email) is not None


def is_valid_phone_number(phone: str) -> bool:
    """
    Checks if the given string is a valid phone number containing only digits.
    """
    phone_regex = r"^[0-9]+$"
    return re.match(phone_regex, phone) is not None


def collect_student_info() -> Dict | None:
    """
    Collects student information using a Streamlit form.

    Returns:
        Dict: A dictionary containing the collected student information, or None if the form is not submitted.
    """
    with st.form("student_form"):
        st.header("Student Information")

        # Basic Information
        name = st.text_input("Full Name", placeholder="Enter your full name")
        contact_info = st.text_input("Email or Phone", placeholder="Your contact details")

        # Academic Background
        st.subheader("Academic Background")
        marks_10th = st.number_input("10th Grade Marks/Percentage", min_value=0, max_value=100, value=None, placeholder="Enter your 10th grade marks")
        marks_12th = st.number_input("12th Grade Marks/Percentage", min_value=0, max_value=100, value=None, placeholder="Enter your 12th grade marks")
        btech_cgpa = st.number_input("B.Tech CGPA (if applicable)", min_value=0.0, max_value=10.0, step=0.1, value=None, placeholder="Enter your CGPA")
        btech_branch = st.text_input("B.Tech Branch (if applicable)", placeholder="Enter your B.Tech branch")

        # Standardized Test Scores
        st.subheader("Standardized Test Scores (Optional)")
        ielts_score = st.number_input("IELTS Score (Optional)", min_value=0.0, max_value=9.0, step=0.1, value=None, placeholder="Enter your IELTS score (optional)")
        toefl_score = st.number_input("TOEFL Score (Optional)", min_value=0, value=None, placeholder="Enter your TOEFL score (optional)")

        # Work Experience
        st.subheader("Work Experience (Optional)")
        work_experience = st.text_area("Work Experience (Optional)", placeholder="Describe your work experience")

        # Preferences
        st.subheader("Preferences")
        preferred_countries = st.multiselect("Preferred Countries", ["USA", "UK", "Australia"], placeholder="Select preferred countries")

        # Interested Field for Masters
        interested_field_for_masters = st.text_input("Interested Field for Masters", placeholder="Enter your preferred field of study")

        submitted = st.form_submit_button("Submit")

        if submitted:
            if not name:
                st.error("Name cannot be empty")
                return None
            if not contact_info:
                st.error("Contact information cannot be empty")
                return None

            # Validate email or phone
            if "@" in contact_info:
                if not is_valid_email(contact_info):
                    st.error("Please enter a valid email address.")
                    return None
            elif not is_valid_phone_number(contact_info):
                st.error("Please enter a valid phone number (only digits).")
                return None
            
            try:
                return {
                    'name': name,
                    'contact_info': contact_info,
                    'marks_10th': int(marks_10th) if marks_10th is not None else 0,
                    'marks_12th': int(marks_12th) if marks_12th is not None else 0,
                    'btech_cgpa': float(btech_cgpa) if btech_cgpa is not None else 0.0,
                    'ielts_score': float(ielts_score) if ielts_score is not None else None,
                    'toefl_score': int(toefl_score) if toefl_score is not None else None,
                    'work_experience': work_experience,
                    'preferred_countries': preferred_countries,
                    'btech_branch': btech_branch,
                    'interested_field_for_masters': interested_field_for_masters,
                    'university_urls': {},
                    'university_details': []
                }
            except Exception as e:
                logging.error(f"Error creating student info dictionary: {e}")
                st.error(f"Error creating student info dictionary: {e}")
                return None

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
                # Define all columns from StudentInfo model
                columns = {
                    'name': 'TEXT',
                    'contact_info': 'TEXT',
                    'marks_10th': 'INTEGER',
                    'marks_12th': 'INTEGER',
                    'btech_cgpa': 'REAL',
                    'ielts_score': 'REAL',
                    'toefl_score': 'REAL',
                    'work_experience': 'TEXT',
                    'preferred_countries': 'TEXT',  # Will store as JSON string
                    'btech_branch': 'TEXT',
                    'interested_field_for_masters': 'TEXT',
                    'university_urls': 'TEXT',  # Will store as JSON string
                    'university_details': 'TEXT'  # Will store as JSON string
                }
                db.create_table(table_name, columns)
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
        student_data = {
            'name': "Test User",
            'contact_info': "test@example.com",
            'marks_10th': 90,
            'marks_12th': 92,
            'btech_cgpa': 8.5,
            'ielts_score': 7.0,
            'toefl_score': 100,
            'work_experience': "2 years",
            'preferred_countries': ["USA"],
            'btech_branch': "Computer Science",
            'interested_field_for_masters': "Computer Science",
            'university_urls': {},
            'university_details': []
        }

    if student_data:
        st.session_state.student_data = student_data # Store student data in session state
        st.success("Form Submitted Successfully!")
        st.subheader("Your Information:")
        if isinstance(student_data, dict):
            st.write(f"Full Name: {student_data.get('name', 'N/A')}")
            st.write(f"Contact Email/Phone: {student_data.get('contact_info', 'N/A')}")
            st.write(f"10th Grade Marks/Percentage: {student_data.get('marks_10th', 'N/A')}")
            st.write(f"12th Grade Marks/Percentage: {student_data.get('marks_12th', 'N/A')}")
            st.write(f"B.Tech CGPA: {student_data.get('btech_cgpa', 'N/A')}")
            st.write(f"IELTS Score: {student_data.get('ielts_score', 'N/A')}")
            st.write(f"TOEFL Score: {student_data.get('toefl_score', 'N/A')}")
            st.write(f"Work Experience: {student_data.get('work_experience', 'N/A')}")
            preferred_countries = student_data.get('preferred_countries', [])
            st.write(f"Preferred Countries: {', '.join(preferred_countries) if preferred_countries else 'N/A'}")
            st.write(f"B.Tech Branch: {student_data.get('btech_branch', 'N/A')}")
            st.write(f"Interested Field for Masters: {student_data.get('interested_field_for_masters', 'N/A')}")
        else:
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
            data = student_data
            db.clear_table(table_name)
            db.insert_data(table_name, data, StudentInfo)
            st.success("Data Saved to Database!")
        except Exception as e:
            st.error(f"Error saving the data: {e}")
            logging.error(f"Error saving the data: {e}")
