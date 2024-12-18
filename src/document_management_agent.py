import streamlit as st
from src.models import Document

def manage_documents():
    documents = [
        Document(name="10th Marksheet", status="pending"),
        Document(name="12th Marksheet", status="pending"),
        Document(name="B.Tech Transcripts", status="pending"),
        Document(name="IELTS/TOEFL Scorecard", status="pending"),
        Document(name="Passport Copy", status="pending"),
    ]

    st.header("Document Management")

    for doc in documents:
        st.write(f"**{doc.name}**: {doc.status}")
        if st.checkbox(f"Uploaded {doc.name}", key=doc.name):
            doc.status = "uploaded"
            st.success(f"Uploaded {doc.name}")
    return documents