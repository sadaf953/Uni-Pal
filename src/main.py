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
from src.graph_workflow import get_workflow
import logging
from typing import Optional
from src.agents.university_recommendation_agent import recommend_universities
from src.llm_interface import query_llm
from src.utils import scrape_website # Add the import here.
settings.LLM_PROVIDER = "groq" # Explicitly set LLM_PROVIDER to groq
logging.info(f"LLM_PROVIDER set to : {settings.LLM_PROVIDER}")


def main():
    """
    Main function to run the Streamlit application.
    """
    st.title("Student Information Form")

    db = Database()
    table_name = "student_info"

    # Check if table exists, create if it doesn't
    if 'table_created' not in st.session_state:
        try:
            db.connect()
            cursor = db.conn.cursor()
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            table_exists = cursor.fetchone()
            if not table_exists:
                columns = StudentInfo.model_fields
                db.create_table(table_name, columns={key: "TEXT" for key in columns})
                logging.info(f"Table {table_name} created.")
            st.session_state.table_created = True
        except Exception as e:
            logging.error(f"Error during table creation: {e}")
            st.error(f"Error during table creation: {e}")
        finally:
            db.close()
    
    skip_student_info = st.button("Skip Student Info")
    if skip_student_info:
      st.session_state.skip_student_info = True


    student_data: Optional[StudentInfo] = None
    if not st.session_state.get("skip_student_info", False):
      student_data = collect_student_info()
    else:
      student_data = StudentInfo(
           name="Test User",
           contact_info="test@example.com",
           marks_10th=90,
           marks_12th=92,
           btech_cgpa=8.5,
           ielts_score=7.0,
           toefl_score=100,
           work_experience="2 years",
           preferred_countries=["USA"],
           btech_branch="Computer Science",
           interested_field_for_masters="Computer Science"
       )


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
        st.write(f"**Interested Field for Masters:** {student_data.interested_field_for_masters if student_data.interested_field_for_masters else 'N/A'}")

        try:
            data = student_data.model_dump()
            # Clear existing data before inserting
            db.clear_table(table_name)
            db.insert_data(table_name, data, StudentInfo)
            st.success("Data Saved to Database!")
        except Exception as e:
            st.error(f"Error saving the data: {e}")
            logging.error(f"Error saving the data: {e}")
        
        if st.button("Test LLM"):
           try:
            llm_response = query_llm("Test LLM")
            st.info(f"LLM Response: {llm_response}")
           except Exception as e:
            st.error(f"Error testing LLM: {e}")
            logging.error(f"Error testing LLM: {e}")
        
        if st.button("Test Selenium"):
            try:
              html = scrape_website("https://www.example.com")
              st.info(f"Selenium response: {html}")
            except Exception as e:
                st.error(f"Error testing selenium: {e}")
                logging.error(f"Error testing selenium: {e}")

        test_url = st.text_input("Test Website URL", placeholder="Enter a URL to test")
        if st.button("Test Web Scrape", key="test_scrape"):
            try:
                 html = scrape_website(test_url)
                 st.info(f"Scrape response: {html}")
            except Exception as e:
                st.error(f"Error scraping {test_url}: {e}")
                logging.error(f"Error scraping {test_url}: {e}")
        
        test_scrape_url = st.text_input("Test URL for University Recommendations", placeholder="Enter a URL to test the scraping")
        if st.button("Test URL Scraping"):
            try:
                test_student_data = StudentInfo(
                    name="Test User",
                    contact_info="test@example.com",
                    marks_10th=90,
                    marks_12th=92,
                    btech_cgpa=8.5,
                    ielts_score=7.0,
                    toefl_score=100,
                    work_experience="2 years",
                    preferred_countries=["USA"],
                    btech_branch="Computer Science",
                    interested_field_for_masters="Computer Science"
                )
                logging.info(f"Testing scraping with URL {test_scrape_url}")
                all_universities_data = []
                search_results = search_web(test_scrape_url)
                if not search_results:
                    logging.warning(f"No search results for {test_scrape_url}")
                
                for result in search_results:
                    university_name = result.get('title', 'N/A').split('|')[0].strip() if result.get('title') else "N/A"
                    url = result.get('link', 'N/A')
                    logging.info(f"University name: {university_name} url: {url}")
                    if url == 'N/A':
                        logging.warning(f"No URL found for {university_name}")
                        continue
                    
                    logging.info(f"Scraping {url} for {university_name}")
                    html = scrape_website(url)
                    
                    if not html:
                        logging.warning(f"Could not scrape page for {university_name}")
                        continue
                    logging.info(f"Got HTML: {html[:500]}")
                    llm_prompt = f"""
                    Extract the following information from the HTML, and return in the format I requested:
                    1. University Name
                    2. Country
                    3. Tuition Fees (Mention Currency)
                    4. Eligibility Criteria (B.Tech CGPA, IELTS and TOEFL requirements)
                    5. Deadlines
                    6. Course Curriculum
                    7. Scholarship options
                    """
                    logging.info(f"Extracting details using LLM for {university_name}")
                    llm_response = extract_content_with_ai(html, llm_prompt) # Used extract_content_with_ai instead of extract_course_details

                    if not llm_response:
                      logging.warning(f"No LLM response for {university_name}")
                      continue

                    try:
                        lines = llm_response.get('extracted_content', " ").split('\n')
                        university_name_llm = lines[0].replace("1. University Name: ", "").strip() if len(lines) > 0 else 'N/A'
                        country = lines[1].replace("2. Country: ", "").strip() if len(lines) > 1 else 'N/A'
                        tuition_fees = lines[2].replace("3. Tuition Fees: ", "").strip() if len(lines) > 2 else 'N/A'
                        eligibility_criteria = lines[3].replace("4. Eligibility Criteria: ", "").strip() if len(lines) > 3 else 'N/A'
                        deadlines = lines[4].replace("5. Deadlines: ", "").strip() if len(lines) > 4 else 'N/A'
                        course_curriculum = lines[5].replace("6. Course Curriculum: ", "").strip() if len(lines) > 5 else 'N/A'
                        scholarship_options = lines[6].replace("7. Scholarship options: ", "").strip() if len(lines) > 6 else 'N/A'

                        university_data = {
                           "university_name": university_name_llm,
                            "university_url": course_url,
                            "country": country,
                            "tuition_fees_usd": tuition_fees,
                            "cgpa_requirement": eligibility_criteria,
                            "deadlines": deadlines,
                            "course_curriculum": course_curriculum,
                            "scholarship_options": scholarship_options
                           }
                        all_universities_data.append(university_data)
                        st.json(university_data)
                    except Exception as e:
                         st.error(f"Error parsing LLM output for {university_name}: {e}")
                         logging.error(f"Error parsing LLM output for {university_name}: {e}")
            except Exception as e:
                st.error(f"Error testing scraping with URL {test_scrape_url}: {e}")
                logging.error(f"Error testing scraping with URL {test_scrape_url}: {e}")


        if st.button("Next Step: University Recommendations"):
           st.session_state.next_step = True
           st.info(f"Button Clicked, next_step set to: {st.session_state.next_step}")


        if st.session_state.get('next_step', False):
            try:
                # Get university recommendations and save the information in universities.csv
                recommendations = recommend_universities(student_data)
                if not recommendations:
                    st.error("No universities found based on the given preferences. Please check the logs for more details.")
                    return
                logging.info("About to invoke LangGraph workflow")
                workflow = get_workflow()
                result = workflow.invoke(student_data.model_dump())
                logging.info("LangGraph workflow invoked successfully")
                st.session_state.workflow_completed = True
            except Exception as e:
                st.error(f"Error running the workflow: {e}")
                logging.error(f"Error running the workflow: {e}")
        if st.session_state.get('workflow_completed', False):
            st.success("Workflow Completed")


if __name__ == "__main__":
    if 'next_step' not in st.session_state:
      st.session_state.next_step = False
    if 'workflow_completed' not in st.session_state:
        st.session_state.workflow_completed = False
    if 'table_created' not in st.session_state:
        st.session_state.table_created = False
    if 'skip_student_info' not in st.session_state:
        st.session_state.skip_student_info = False
    main()