import streamlit as st
from src.models import StudentInfo
import logging
import re

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


def collect_student_info() -> StudentInfo | None:
    """
    Collects student information using a Streamlit form.

    Returns:
        StudentInfo: An object containing the collected student information, or None if the form is not submitted.
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
                 student_info = StudentInfo(
                    name=name,
                    contact_info=contact_info,
                    marks_10th=marks_10th,
                    marks_12th=marks_12th,
                    btech_cgpa=btech_cgpa,
                    ielts_score=float(ielts_score) if ielts_score else None,
                    toefl_score=float(toefl_score) if toefl_score else None,
                    work_experience=work_experience,
                    preferred_countries=preferred_countries,
                    btech_branch=btech_branch,
                    interested_field_for_masters=interested_field_for_masters,
                )
                 return student_info
            except Exception as e:
                logging.error(f"Error creating student info object: {e}")
                st.error(f"Error creating student info object: {e}")
                return None

    return None