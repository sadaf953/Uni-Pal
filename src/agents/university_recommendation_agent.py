import os
import logging
from pydoc import writedoc
from dotenv import load_dotenv
import streamlit as st
from src.utils import scrape_website, extract_content_with_ai, clean_search_results
from src.llm_interface import query_llm
from src.config import settings
from src.graph_workflow import get_workflow
import json 
import pandas as pd
import csv
from urllib.parse import urlparse


# Load environment variables
load_dotenv()

def save_raw_results(data):
    with open('raw_results.json', 'w') as f:
        json.dump(data, f)

def load_raw_results():
    try:
        with open('raw_results.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def scraping_testing_page():
    st.title("Scraping and Searching Tests")

    if st.button("Test LLM"):
        try:
            llm_response = query_llm("Test LLM")
            st.info(f"LLM Response: {llm_response}")
        except Exception as e:
            st.error(f"Error testing LLM: {e}")
            logging.error(f"Error testing LLM: {e}")

    if st.button("Use Predefined URL"):
        st.session_state.test_url = "https://postgraduate.degrees.ed.ac.uk/?id=107%2520&r=site/view&edition=2025"

    test_url = st.text_input("Test Website URL", placeholder="Enter a URL to test", value=st.session_state.get('test_url', ''))

    if st.button("Run All Steps"):
        try:
            st.info("Starting raw data scraping...")
            raw_results = scrape_website(test_url)
            st.success("Raw data scraped successfully.")

            st.info("Saving raw results...")
            st.session_state.raw_results = {
                "web_search_results": {
                    "raw_data": raw_results
                }
            }
            save_raw_results(st.session_state.raw_results)  # Save raw results locally
            st.success("Raw results saved successfully.")

            st.info("Cleaning raw results...")
            cleaned_results = clean_search_results(st.session_state.raw_results)
            st.session_state.cleaned_results = cleaned_results
            st.success("Cleaned results generated successfully.")

            st.info("Extracting content with AI...")
            extracted_content = extract_content_with_ai(cleaned_results['web_search_results']['raw_data'], 'Extract relevant information')
            st.session_state.extracted_content = extracted_content
            st.success("Content extracted successfully.")
            st.write(extracted_content.get('extracted_content', 'No content extracted.'))

        except Exception as e:
            st.error(f"Error in processing: {e}")
            logging.error(f"Error in processing: {e}")

    if st.session_state.get('next_step', False):
        try:
            logging.info("About to invoke LangGraph workflow")
            workflow = get_workflow()
            # Assuming student_data is available in st.session_state from the previous page
            student_data = st.session_state.get('student_data')
            if student_data:
                result = workflow.invoke({"student_info": student_data})
                logging.info("LangGraph workflow invoked successfully")
                st.session_state.workflow_completed = True
                st.write(f"Result from LangGraph {result}")
            else:
                st.warning("Student data not found. Please complete the Student Information page.")
        except Exception as e:
            st.error(f"Error running the workflow: {e}")
            logging.error(f"Error running the workflow: {e}")

    if st.session_state.get('workflow_completed', False):
        st.success("Workflow Completed")

    st.subheader("Get Links based on Input")
    search_input = st.text_input("Enter text to search for relevant links:")
    if st.button("Search Links"):
        if search_input:
            with st.spinner("Searching for links..."):
                api_key = settings.TRAVILY_API_KEY
                if api_key:
                    search_results = travily_search(search_input, api_key)
                    if search_results:
                        st.success("Search complete. Found links:")
                        for link in search_results:
                            st.write(link)
                    else:
                        st.info("No relevant links found.")
                else:
                    st.error("Travily API key is not configured. Please check your settings.")
        else:
            st.warning("Please enter text to search for links.")


def process_all_university_links():
    """
    Process all university links from processed_universities.csv
    and extract content for each link.
    """
    st.title("Process All University Links")
    # Create scraping results directory if it doesn't exist
    scraping_dir = os.path.join(os.getcwd(),'scraping_results')
    os.makedirs(scraping_dir, exist_ok=True)
    try:
        # Read the CSV file
        df = pd.read_csv('processed_universities.csv')
        # Check if 'URL' column exists
        if 'URL' not in df.columns:
            st.error("No 'URL' column found in the CSV file.")
            return
        # Create a progress bar
        progress_bar = st.progress(0)
        results = []
        # Process each URL
        for index, row in df.iterrows():
            url = row['URL']
            try:
                # Update progress bar
                progress_bar.progress((index + 1) / len(df))
                st.write(f"Processing: {url}")
                # Scrape website
                raw_results = scrape_website(url)
                # Clean results
                cleaned_results = clean_search_results({
                    "web_search_results": {
                        "raw_data": raw_results
                    }
                })
                # Extract content with AI
                extracted_content = extract_content_with_ai(
                    cleaned_results['web_search_results']['raw_data'], 
                    'Extract university program information'
                )
                # Generate a safe filename from the URL
                parsed_url = urlparse(url)
                safe_filename = f"{parsed_url.netloc.replace('.', '_')}_details.csv"
                file_path = os.path.join(scraping_dir, safe_filename)
                # Save individual university details to CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    # Flatten the extracted content
                    writer = csv.DictWriter(csvfile, fieldnames=['key', 'value'])
                    writer.writeheader()
                    
                    # Write source URL
                    writer.writerow({'key': 'Source URL', 'value': url})
                    
                    # Write timestamp
                    writer.writerow({'key': 'Timestamp', 'value': extracted_content.get('timestamp', '')})
                    
                    # If extracted_content is a dictionary, write its contents
                    if isinstance(extracted_content.get('extracted_content'), dict):
                        for key, value in extracted_content['extracted_content'].items():
                            writer.writerow({'key': key, 'value': str(value)})
                    else:
                        # If it's a string or something else, write it as a single value
                        writer.writerow({'key': 'Extracted Content', 'value': str(extracted_content.get('extracted_content', ''))})
                
                # Add to results
                extracted_content['source_url'] = url
                results.append(extracted_content)
                
                # Optional: Save intermediate results
                with open('all_university_results.json', 'w') as f:
                    json.dump(results, f, indent=2)
                
            except Exception as e:
                st.error(f"Error processing {url}: {e}")
                logging.error(f"Error processing {url}: {e}")
        
        # Complete progress bar
        progress_bar.progress(100)
        # Display results
        st.subheader("Processed Results")
        st.json(results)
        # Save final results
        with open('all_university_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        st.success(f"Processed {len(results)} university links successfully!")
        st.info(f"Individual university details saved in {scraping_dir}")
    except FileNotFoundError:
        st.error("processed_universities.csv not found. Please run university search first.")
    except Exception as e:
        st.error(f"An error occurred: {e}")
        logging.error(f"Error in processing university links: {e}")



def recommend_top_universities(student_data):
    """
    Analyzes and recommends top 5 universities based on scraped data and student profile.

    Args:
        student_data (dict): A dictionary containing the student's information.

    Returns:
        pd.DataFrame: Recommended universities with key details.
    """

    # Collect university details from scraping results
    scraping_dir = os.path.join(os.getcwd(), 'scraping_results')
    university_details = []

    for filename in os.listdir(scraping_dir):
        if filename.endswith('_details.csv'):
            file_path = os.path.join(scraping_dir, filename)
            try:
                df = pd.read_csv(file_path)
                uni_info = df.set_index('key')['value'].to_dict()
                university_details.append(uni_info)
            except Exception as e:
                print(f"Error reading or processing {filename}: {e}")

    universities_df = pd.DataFrame(university_details)

    # Basic recommendation logic (can be enhanced)
    # This is a placeholder, implement more sophisticated logic
    ranked_universities = []
    for index, uni in universities_df.iterrows():
        score = 0
        # Example: Check if student's preferred major is in the curriculum
        if student_data.get('preferred_major') and uni.get('course_curriculum', '').lower().__contains__(student_data['preferred_major'].lower()):
            score += 1

        # Example: Check if student meets basic eligibility (can be more complex)
        # This assumes student_data has fields like 'gpa', 'test_scores'
        if student_data.get('gpa') and uni.get('eligibility_criteria', '').lower().__contains__('gpa'):
            try:
                # Very basic check - assumes eligibility mentions 'GPA' and a value
                uni_gpa_req = float(''.join(filter(str.isdigit or str.isalpha or str.isspace or (lambda c: c in ['.']), uni.get('eligibility_criteria', '').lower().split('gpa')[1].split()[0])))
                if student_data['gpa'] >= uni_gpa_req:
                    score += 1
            except:
                pass # Could not parse GPA requirement

        # Consider tuition fees (can compare with student's budget if available)
        # This is a very basic check, you'll need to parse the fee strings
        if uni.get('tuition_fees', 'N/A') != 'N/A':
            try:
                # Very basic fee comparison - assumes a simple numerical fee
                uni_fees = float(''.join(filter(str.isdigit, uni['tuition_fees'])))
                # Example: Lower fees might be preferred (can adjust logic)
                if student_data.get('budget') and uni_fees <= student_data['budget']:
                    score += 1
            except:
                pass

        ranked_universities.append((uni, score))

    # Sort universities by score (higher score is better)
    ranked_universities.sort(key=lambda item: item[1], reverse=True)

    # Select top 5 universities
    top_5_universities = [item[0] for item in ranked_universities[:5]]

    # Prepare the output DataFrame
    recommendations_data = []
    for uni in top_5_universities:
        recommendations_data.append({
            'University Name': uni.get('university_name', 'N/A'),
            'Fees': uni.get('tuition_fees', 'N/A'),
            'Curriculum': uni.get('course_curriculum', 'N/A'),
            'Eligibility': uni.get('eligibility_criteria', 'N/A'),
            'Scholarships Available': uni.get('scholarship_options', 'N/A')
        })

    recommendations_df = pd.DataFrame(recommendations_data)
    return recommendations_df

