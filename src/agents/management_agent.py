import streamlit as st
from src.models import Document, University
from typing import List, Dict, Optional
import logging
from typing import List
from src.utils import safe_log
import pandas as pd


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

def filter_and_rank_universities(student_info: Dict, universities: List[University]) -> List[University]:
    """
    Filters and ranks universities based on student information and university data.
    
    Args:
        student_info (Dict): Student information dictionary
        universities (List[University]): List of University objects.
        
    Returns:
        List[University]: List of top 5 recommended universities.
    """
    
    if not universities or not student_info:
        safe_log("No universities or student info to filter")
        return []
    
    df = pd.DataFrame([to_dict(uni) for uni in universities])

    # Convert tuition fees to int, handling N/A values
    df['tuition_fees'] = df['tuition_fees'].replace('N/A', 0).astype(float)


    # Create a dictionary for currency conversion
    currency_map = {
        "USA": "USD",
        "UK": "GBP",
        "Australia": "AUD",
    }

    df["currency"] = df["country"].map(currency_map)

    def convert_fees(row):
        if row['currency'] is None:
            logging.warning(f"No currency found for {row['university_name']}")
            return None
        return row['tuition_fees']

    df["tuition_fees_inr"] = df.apply(convert_fees, axis=1)

    df["score"] = 0
    for index, row in df.iterrows():
        score = 0
        if row["country"] in student_info.get('preferred_countries', []):
            score += 10
        if 'eligibility_criteria' in row and isinstance(row['eligibility_criteria'], str):
            try:
                cgpa = float(row['eligibility_criteria'].split("CGPA")[0].strip().split("with")[-1].strip())
                if cgpa <= student_info.get('btech_cgpa', 0):
                    score += 10
            except:
                logging.warning(f"Could not parse cgpa requirement for {row['name']}")
        if 'ielts_requirement' in row and isinstance(row['eligibility_criteria'], str):
            try:
                ielts = float(row['eligibility_criteria'].split("IELTS")[1].strip().split("+")[0].strip())
                if student_info.get('ielts_score') is not None and ielts <= student_info.get('ielts_score', 0):
                    score += 5
            except:
                logging.warning(f"Could not parse ielts requirement for {row['name']}")

        if 'toefl_requirement' in row and isinstance(row['eligibility_criteria'], str):
            try:
                toefl = float(row['eligibility_criteria'].split("TOEFL")[1].strip().split("+")[0].strip())
                if student_info.get('toefl_score') is not None and toefl <= student_info.get('toefl_score', 0):
                    score += 5
            except:
                logging.warning(f"Could not parse toefl requirement for {row['name']}")
        
        # Add score based on interested field for Masters if available
        if student_info.get('interested_field_for_masters'):
            score += 3
        
        df.loc[index, 'score'] = score

    df = df.sort_values(by="score", ascending=False)

    recommended_universities = df.head(5)

    universities = [
        University(**row.to_dict())
        for index, row in recommended_universities.iterrows()
    ]

    return universities


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
        
        # Mock data if universities are not present
        if not universities:
            safe_log("Using mock universities data")
            universities = [
                 University(
                    name="University A",
                    url="https://www.example.com/universityA",
                    tuition_fees="10000",
                    currency='USD',
                    eligibility_criteria="B.Tech with 8.0 CGPA or above, IELTS 7.0+, TOEFL 100+",
                    deadlines="2024-12-31",
                    course_curriculum="Curriculum A",
                    scholarship_options="Scholarship A"
                ),
                University(
                    name="University B",
                    url="https://www.example.com/universityB",
                    tuition_fees="12000",
                     currency='USD',
                    eligibility_criteria="B.Tech with 8.5 CGPA or above, IELTS 7.5+, TOEFL 105+",
                    deadlines="2024-11-30",
                    course_curriculum="Curriculum B",
                    scholarship_options="Scholarship B"
                 ),
                 University(
                    name="University C",
                     url="https://www.example.com/universityC",
                    tuition_fees="12000",
                     currency='USD',
                    eligibility_criteria="B.Tech with 8.5 CGPA or above, IELTS 7.5+, TOEFL 105+",
                    deadlines="2024-11-30",
                    course_curriculum="Curriculum B",
                    scholarship_options="Scholarship B"
                 ),
                University(
                    name="University D",
                    url="https://www.example.com/universityD",
                    tuition_fees="12000",
                     currency='USD',
                    eligibility_criteria="B.Tech with 8.5 CGPA or above, IELTS 7.5+, TOEFL 105+",
                    deadlines="2024-11-30",
                    course_curriculum="Curriculum B",
                    scholarship_options="Scholarship B"
                 ),
                University(
                    name="University E",
                   url="https://www.example.com/universityE",
                    tuition_fees="12000",
                     currency='USD',
                    eligibility_criteria="B.Tech with 8.5 CGPA or above, IELTS 7.5+, TOEFL 105+",
                    deadlines="2024-11-30",
                    course_curriculum="Curriculum B",
                    scholarship_options="Scholarship B"
                 ),
            ]
        # Filter and rank universities
        if universities and student_info:
             ranked_universities = filter_and_rank_universities(student_info, universities)
        else:
            ranked_universities = universities if universities else []

        # Display overall application state
        st.header("Application Progress Dashboard")

        # Student Information
        if student_info:
            with st.expander("Student Information"):
                st.write(f"**Name:** {student_info.get('name', 'N/A')}")
                st.write(f"**Contact:** {student_info.get('contact_info', 'N/A')}")
                st.write(f"**B.Tech Branch:** {student_info.get('btech_branch', 'N/A')}")

        # Universities
        if ranked_universities:
            with st.expander("University Recommendations"):
                for univ in ranked_universities:
                     st.write(f"**{univ.name}**")
                     st.write(f"Tuition Fees: {univ.tuition_fees}")
                     st.write(f"Eligibility : {univ.eligibility_criteria}")
                     st.write(f"Course Curriculum: {univ.course_curriculum}")


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
            bool(ranked_universities),
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
            'universities': ranked_universities or [],
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