import streamlit as st
from src.models import ScholarshipInfo
from src.utils import query_llm

def fetch_scholarship_info(student_info):
    """
    Fetch scholarship information based on student profile
    
    Args:
        student_info (dict or StudentInfo): Student information
    
    Returns:
        dict: Scholarship information
    """
    # Convert Pydantic model to dictionary if needed
    if hasattr(student_info, 'model_dump'):
        student_info = student_info.model_dump()
    
    # Validate student information
    if not student_info:
        st.warning("Please provide student information first.")
        return {}
    
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
    - IELTS Score: {student_info.get('ielts_score', 'N/A')}
    - TOEFL Score: {student_info.get('toefl_score', 'N/A')}
    - Preferred Countries: {preferred_countries}
    
    Recommend top 3 scholarships that match this student's profile in the preferred countries. 
    For each scholarship, provide:
    1. Scholarship Name
    2. Country
    3. Eligibility Criteria
    4. Award Amount
    5. Application Deadline
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
                        'country': entry.split('\n')[1].replace('Country: ', '').strip(),
                        'eligibility_criteria': entry.split('\n')[2].replace('Eligibility Criteria: ', '').strip(),
                        'award_amount': entry.split('\n')[3].replace('Award Amount: ', '').strip(),
                        'application_deadline': entry.split('\n')[4].replace('Application Deadline: ', '').strip()
                    })
                    scholarships.append(scholarship)
                except Exception as e:
                    st.warning(f"Could not parse scholarship entry: {entry}")
        
        # Display scholarships in Streamlit
        st.subheader("Recommended Scholarships")
        for scholarship in scholarships:
            with st.expander(f"{scholarship.name} ({scholarship.country})"):
                st.write(f"**Eligibility Criteria:** {scholarship.eligibility_criteria}")
                st.write(f"**Award Amount:** {scholarship.award_amount}")
                st.write(f"**Application Deadline:** {scholarship.application_deadline}")
        
        # Return a dictionary representation of scholarships
        return {
            'scholarships': [scholarship.model_dump() for scholarship in scholarships]
        }
    
    except Exception as e:
        st.error(f"Error generating scholarship recommendations: {e}")
        return {}