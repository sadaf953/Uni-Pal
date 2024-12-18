import streamlit as st
from src.models import Document

def display_results(universities, visa_info, scholarships, documents):
    st.header("Results")
    st.subheader("University Recommendations")
    for uni in universities:
        st.write(f"- {uni.name}")
        st.write(f"  - Curriculum: {uni.course_curriculum}")
        st.write(f"  - Scholarships: {uni.scholarship_options}")
        if uni.tuition_fees:
          st.write(f"  - Tuition Fees: {uni.tuition_fees}")

    st.subheader("Visa Requirements")
    if visa_info:
        st.write(f"**Country**: {visa_info.country}")
        st.write("**Requirements**: ")
        for doc in visa_info.requirements:
            st.write(f"- {doc}")
    else:
        st.write("Visa requirements not available.")

    st.subheader("Scholarships")
    if scholarships:
       for scholar in scholarships:
            st.write(f"**{scholar.name}**: {scholar.description}")
    else:
        st.write("No scholarships found.")

    st.subheader("Documents")
    for doc in documents:
      st.write(f"**{doc.name}**: {doc.status}")


def manage_state(student_info=None, universities=None, visa_info=None, scholarships=None, documents=None):
    """
    Manage and display the overall state of the student's application process
    
    Args:
        student_info (dict, optional): Student information
        universities (list, optional): Recommended universities
        visa_info (dict, optional): Visa information
        scholarships (list, optional): Recommended scholarships
        documents (list, optional): Document status
    
    Returns:
        dict: Consolidated application state
    """
    # Convert inputs to dictionaries if they are Pydantic models
    if hasattr(student_info, 'model_dump'):
        student_info = student_info.model_dump()
    if universities and hasattr(universities[0], 'model_dump'):
        universities = [univ.model_dump() for univ in universities]
    if visa_info and hasattr(visa_info, 'model_dump'):
        visa_info = visa_info.model_dump()
    if scholarships and hasattr(scholarships[0], 'model_dump'):
        scholarships = [schol.model_dump() for schol in scholarships]
    if documents and hasattr(documents[0], 'model_dump'):
        documents = [doc.model_dump() for doc in documents]
    
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
                st.write(f"**{univ.get('name', 'N/A')}** ({univ.get('country', 'N/A')})")
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
                st.write(f"Award Amount: {schol.get('award_amount', 'N/A')}")
    
    # Documents
    if documents:
        with st.expander("Document Management"):
            for doc in documents:
                status_color = "green" if doc.get('status', 'Pending') == "Completed" else "orange"
                st.markdown(f"**{doc.get('name', 'N/A')}**: <font color='{status_color}'>{doc.get('status', 'Pending')}</font>", unsafe_allow_html=True)
    
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
    return {
        'student_info': student_info or {},
        'universities': universities or [],
        'visa_info': visa_info or {},
        'scholarships': scholarships or [],
        'documents': documents or [],
        'progress_percentage': progress_percentage
    }