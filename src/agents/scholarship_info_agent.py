import streamlit as st
from src.models import ScholarshipInfo
from src.utils import query_llm
import logging
from typing import List, Optional

def fetch_scholarship_info(student_info) -> Optional[List[ScholarshipInfo]]:
    """
    Fetch scholarship information based on student profile.

    Args:
        student_info: Student information.

    Returns:
        A list of ScholarshipInfo objects, or None if there is an error or no scholarships are found.
    """
    # Convert Pydantic model to dictionary if needed
    if hasattr(student_info, 'model_dump'):
        student_info = student_info.model_dump()

    # Validate student information
    if not student_info:
        logging.warning("Please provide student information first.")
        return None

    # Extract preferred countries or use a default
    preferred_countries = student_info.get('preferred_countries', ['USA'])

    # Prepare the prompt for scholarship recommendations
    prompt = f"""
    Based on the following student profile:
    - Name: {student_info.get('name', 'N/A')}
    - 10th Marks: {student_info.get('marks_10th', 'N/A')}
    - 12th Marks: {student_info.get('marks_12th', 'N/A')}
    - B.Tech CGPA: {student_info.get('btech_cgpa', 'N/A')}
    - B.Tech Branch: {student_info.get('btech_branch', 'N/A')}
    - Interested Field for Masters: {student_info.get('interested_field_for_masters', 'N/A')}
    - Work Experience: {student_info.get('work_experience', 'N/A')}
    - IELTS Score: {student_info.get('ielts_score', 'N/A')}
    - TOEFL Score: {student_info.get('toefl_score', 'N/A')}
    - Preferred Countries: {preferred_countries}

    Recommend top 3 scholarships that match this student's profile in the preferred countries.
    For each scholarship, provide:
    1. Scholarship Name
    2. Description
    3. Eligibility Criteria
    4. Award Amount
    """
    # Query the LLM for scholarship recommendations
    try:
        llm_response = query_llm(prompt)

        # Parse the LLM response into a list of scholarship dictionaries
        scholarships = []
        for entry in llm_response.split('\n\n'):
            if entry.strip():
                try:
                    # Create a ScholarshipInfo object from the parsed entry
                    scholarship = ScholarshipInfo(**{
                        'name': entry.split('\n')[0].replace('1. ', '').strip(),
                        'description': entry.split('\n')[1].replace('2. ', '').strip(),
                        'eligibility': entry.split('\n')[2].replace('3. ', '').strip(),
                        'amount': entry.split('\n')[3].replace('4. ', '').strip()
                    })
                    scholarships.append(scholarship)
                except Exception as e:
                    logging.warning(f"Could not parse scholarship entry: {entry}")
        return scholarships

    except Exception as e:
        logging.error(f"Error generating scholarship recommendations: {e}")
        return None