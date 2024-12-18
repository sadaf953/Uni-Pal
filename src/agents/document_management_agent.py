import streamlit as st
from src.models import Document

def manage_documents(student_info=None):
    """
    Manage and display document requirements for the student
    
    Args:
        student_info (dict or StudentInfo, optional): Student information
    
    Returns:
        dict: Document management information
    """
    # Convert Pydantic model to dictionary if needed
    if hasattr(student_info, 'model_dump'):
        student_info = student_info.model_dump()
    
    # Define a list of standard documents required for university applications
    standard_documents = [
        Document(
            name="10th Grade Marksheet",
            status="Pending",
            required=True,
            description="Official marksheet/transcript from 10th grade"
        ),
        Document(
            name="12th Grade Marksheet",
            status="Pending",
            required=True,
            description="Official marksheet/transcript from 12th grade"
        ),
        Document(
            name="B.Tech Degree/Marksheet",
            status="Pending",
            required=True,
            description="Official B.Tech degree or latest semester marksheet"
        ),
        Document(
            name="IELTS/TOEFL Score",
            status="Pending",
            required=True,
            description="English proficiency test score"
        ),
        Document(
            name="Passport",
            status="Pending",
            required=True,
            description="Valid passport for international travel"
        ),
        Document(
            name="Statement of Purpose (SOP)",
            status="Pending",
            required=True,
            description="Personal essay explaining academic and career goals"
        )
    ]
    
    # Display document requirements in Streamlit
    st.subheader("Document Management")
    
    # Create a form to track document status
    with st.form("document_status_form"):
        for doc in standard_documents:
            doc.status = st.selectbox(
                f"{doc.name} Status", 
                ["Pending", "In Progress", "Completed"], 
                index=0 if doc.status == "Pending" else 1 if doc.status == "In Progress" else 2
            )
        
        submitted = st.form_submit_button("Update Document Status")
        if submitted:
            st.success("Document status updated successfully!")
    
    # Display document requirements
    st.write("### Document Requirements")
    for doc in standard_documents:
        with st.expander(f"{doc.name} - {doc.status}"):
            st.write(f"**Description:** {doc.description}")
            st.write(f"**Required:** {'Yes' if doc.required else 'No'}")
    
    # Return a dictionary of document information
    return {
        'documents': [doc.model_dump() for doc in standard_documents]
    }