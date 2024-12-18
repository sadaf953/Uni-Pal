import os
import sys

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

def main():
    st.title("Student Information Form")

    student_data = collect_student_info()

    if student_data:
        st.success("Form Submitted Successfully!")
        st.subheader("Your Information:")
        # Display data in a nice format
        st.write(f"**Full Name:** {student_data.name}")
        st.write(f"**Contact Email/Phone:** {student_data.contact_info}")
        st.write(f"**10th Grade Marks/Percentage:** {student_data.marks_10th}")
        st.write(f"**12th Grade Marks/Percentage:** {student_data.marks_12th}")
        st.write(f"**B.Tech CGPA:** {student_data.btech_cgpa}")
        st.write(f"**IELTS Score:** {student_data.ielts_score if student_data.ielts_score is not None else 'N/A'}")
        st.write(f"**TOEFL Score:** {student_data.toefl_score if student_data.toefl_score is not None else 'N/A'}")
        st.write(f"**Work Experience:** {student_data.work_experience if student_data.work_experience else 'N/A'}")
        st.write(f"**Preferred Countries:** {', '.join(student_data.preferred_countries) if student_data.preferred_countries else 'N/A'}")
        st.write(f"**B.Tech Branch:** {student_data.btech_branch}")
        st.write(f"**Interested Field for Masters:** {student_data.Interested_feild_for_Masters if student_data.Interested_feild_for_Masters else 'N/A'}")

        db = Database()
        columns = student_data.model_fields
        data = student_data.model_dump()
        try:
           print("Clearing the data in the database")
           db.clear_table("student_info")
           print(f"Creating table with {columns}")
           db.create_table("student_info", columns=columns)
           print(f"Saving data {data}")
           db.insert_data("student_info", data, StudentInfo)
           st.success("Data Saved to Database!")
        except Exception as e:
           st.error(f"Error saving the data : {e}")

        if st.button("Next Step: University Recommendations"):
           st.session_state.next_step = True
        if st.session_state.get('next_step', False):
          st.write("Next step logic goes here")


if __name__ == "__main__":
    if 'next_step' not in st.session_state:
      st.session_state.next_step = False
    main()