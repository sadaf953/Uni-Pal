import streamlit as st
from src.models import Document
from typing import List, Dict, Optional
import logging

def to_dict(obj) -> dict:
    """
    Converts a Pydantic model or a list of Pydantic models to dictionaries.
    """
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    if isinstance(obj, list) and obj and hasattr(obj[0], 'model_dump'):
      return [item.model_dump() for item in obj]
    return obj

def display_results(universities: List, visa_info: Optional[Dict], scholarships: Optional[List], documents: Optional[List]):
    """
    Displays the results of the application process using Streamlit.

    Args:
        universities: A list of university objects.
        visa_info: Visa information for the chosen country.
        scholarships: A list of scholarship objects.
        documents: A list of document objects.
    """
    st.header("Results")
    st.subheader("University Recommendations")
    if universities:
        for uni in universities:
            st.write(f"- {uni.get('name', 'N/A')}")
            st.write(f"  - Curriculum: {uni.get('course_curriculum', 'N/A')}")
            st.write(f"  - Scholarships: {uni.get('scholarship_options', 'N/A')}")
            if uni.get('tuition_fees'):
              st.write(f"  - Tuition Fees: {uni.get('tuition_fees', 'N/A')}")
    else:
         st.write("No university recommendations found.")

    st.subheader("Visa Requirements")
    if visa_info:
        st.write(f"**Country**: {visa_info.get('country', 'N/A')}")
        st.write("**Requirements**: ")
        for doc in visa_info.get('requirements', []):
            st.write(f"- {doc}")
    else:
        st.write("Visa requirements not available.")

    st.subheader("Scholarships")
    if scholarships:
       for scholar in scholarships:
            st.write(f"**{scholar.get('name', 'N/A')}**: {scholar.get('description', 'N/A')}")
    else:
        st.write("No scholarships found.")

    st.subheader("Documents")
    if documents:
       for doc in documents:
            st.write(f"**{doc.get('name', 'N/A')}**: {doc.get('status', 'N/A')}")
    else:
        st.write("No documents found.")


def manage_state(student_info: Optional[Dict] = None, universities: Optional[List] = None, visa_info: Optional[Dict] = None, scholarships: Optional[List] = None, documents: Optional[List] = None) -> Dict:
    """
    Manages and displays the overall state of the student's application process, and returns a consolidated state.

    Args:
        student_info: Student information.
        universities: Recommended universities.
        visa_info: Visa information.
        scholarships: Recommended scholarships.
        documents: Document status.

    Returns:
        A dictionary containing the consolidated application state.
    """
    try:
        # Convert all the inputs to dict if they are Pydantic models
        student_info = to_dict(student_info)
        universities = to_dict(universities)
        visa_info = to_dict(visa_info)
        scholarships = to_dict(scholarships)
        documents = to_dict(documents)

        # Display overall application state
        st.header("Application Progress Dashboard")

        # Student Information
        if student_info:
            with st.expander("Student Information"):
                st.write(f"**Name:** {student_info.get('name', 'N/A')}")
                st.write(f"**Contact:** {student_info.get('contact_info', 'N/A')}")
                st.write(f"**B.Tech Branch:** {student_info.get('btech_branch', 'N/A')}")

        # Universities
        if universities:
            with st.expander("University Recommendations"):
                for univ in universities:
                    st.write(f"**{univ.get('name', 'N/A')}**")
                    st.write(f"Tuition Fees: {univ.get('tuition_fees', 'N/A')}")

        # Visa Information
        if visa_info:
            with st.expander("Visa Requirements"):
                st.write(f"**Country:** {visa_info.get('country', 'N/A')}")
                st.write("**Requirements:**")
                for req in visa_info.get('requirements', []):
                    st.write(f"- {req}")

        # Scholarships
        if scholarships:
            with st.expander("Scholarship Opportunities"):
                for schol in scholarships:
                    st.write(f"**{schol.get('name', 'N/A')}**")
                    st.write(f"Award Amount: {schol.get('amount', 'N/A')}")

        # Documents
        if documents:
            with st.expander("Document Management"):
                for doc in documents:
                    status_color = "green" if doc.get('status', 'Pending') == "Completed" else "orange"
                    st.markdown(f"**{doc.get('name', 'N/A')}**: <span style='color:{status_color}'>{doc.get('status', 'Pending')}</span>", unsafe_allow_html=True)

        # Overall Progress
        progress_steps = [
            bool(student_info),
            bool(universities),
            bool(visa_info),
            bool(scholarships),
            bool(documents)
        ]
        progress_percentage = sum(progress_steps) / len(progress_steps) * 100

        st.progress(int(progress_percentage))
        st.write(f"Overall Application Progress: {int(progress_percentage)}%")

        # Return a consolidated state dictionary
        state =  {
            'student_info': student_info or {},
            'universities': universities or [],
            'visa_info': visa_info or {},
            'scholarships': scholarships or [],
            'documents': documents or [],
            'progress_percentage': progress_percentage
        }
        return state
    except Exception as e:
         logging.error(f"Error managing state: {e}")
         st.error(f"Error managing state: {e}")
         return {}