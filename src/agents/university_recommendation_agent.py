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
    Process all university links from processed_universities.csv and extract detailed information
    about programs, requirements, deadlines, and costs.
    """
    st.title("Processing University Information")
    st.write("Extracting detailed information from university websites...")
    
    # Create scraping results directory if it doesn't exist
    scraping_dir = os.path.join(os.getcwd(), 'scraping_results')
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
        status_text = st.empty()
        
        # Initialize results storage
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        # Process each URL
        for index, row in df.iterrows():
            url = row['URL']
            try:
                # Update progress
                progress = (index + 1) / len(df)
                progress_bar.progress(progress)
                status_text.text(f"Processing {index + 1} of {len(df)}: {url}")
                
                # Scrape website with error handling
                try:
                    raw_results = scrape_website(url)
                    if not raw_results:
                        st.warning(f"No content found for {url}")
                        continue
                except Exception as e:
                    st.warning(f"Failed to scrape {url}: {str(e)}")
                    continue
                
                # Clean results
                cleaned_results = clean_search_results({
                    "web_search_results": {
                        "raw_data": raw_results
                    }
                })
                
                # Extract content with AI
                extracted_content = extract_content_with_ai(
                    cleaned_results['web_search_results']['raw_data'],
                    'Extract detailed university program information'
                )
                
                # Generate a safe filename from the URL
                parsed_url = urlparse(url)
                safe_filename = f"{parsed_url.netloc.replace('.', '_')}_details.csv"
                file_path = os.path.join(scraping_dir, safe_filename)
                
                # Save detailed university information to CSV
                content = extracted_content['extracted_content']
                rows = []
                
                # Helper function to flatten nested dictionary
                def flatten_dict(d, parent_key=''):
                    items = []
                    for k, v in d.items():
                        new_key = f"{parent_key}_{k}" if parent_key else k
                        if isinstance(v, dict):
                            items.extend(flatten_dict(v, new_key).items())
                        else:
                            items.append((new_key, v))
                    return dict(items)
                
                # Flatten the content for CSV storage
                flattened_content = flatten_dict(content)
                
                # Write to CSV
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=['key', 'value'])
                    writer.writeheader()
                    
                    # Write metadata
                    writer.writerow({'key': 'source_url', 'value': url})
                    writer.writerow({'key': 'extraction_timestamp', 'value': extracted_content['timestamp']})
                    
                    # Write flattened content
                    for key, value in flattened_content.items():
                        writer.writerow({'key': key, 'value': str(value)})
                
                # Add to results
                results.append({
                    'url': url,
                    'filename': safe_filename,
                    'content': content
                })
                
                successful_extractions += 1
                
                # Save intermediate results
                with open(os.path.join(scraping_dir, 'all_results.json'), 'w') as f:
                    json.dump(results, f, indent=2)
                
            except Exception as e:
                st.error(f"Error processing {url}: {str(e)}")
                logging.error(f"Error processing {url}: {str(e)}", exc_info=True)
                failed_extractions += 1
                continue
        
        # Complete progress bar
        progress_bar.progress(100)
        status_text.text("Processing complete!")
        
        # Display summary
        st.success(f"""
        Processing Complete!
        - Successfully processed: {successful_extractions} universities
        - Failed to process: {failed_extractions} universities
        - Results saved in: {scraping_dir}
        """)
        
        # Create a summary DataFrame
        summary_data = []
        for result in results:
            content = result['content']
            summary_data.append({
                'University': content.get('university_name', 'Unknown'),
                'Program': content.get('program_details', {}).get('name', 'Not specified'),
                'Duration': content.get('program_details', {}).get('duration', 'Not specified'),
                'Deadline': content.get('deadlines', {}).get('regular', 'Not specified'),
                'Tuition': content.get('tuition_fees', {}).get('total_cost', 'Not specified')
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.subheader("Quick Summary of Extracted Information")
        st.dataframe(summary_df)
        
        return results
        
    except FileNotFoundError:
        st.error("processed_universities.csv not found. Please run university search first.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        logging.error(f"Error in processing university links: {str(e)}", exc_info=True)
        return None


def recommend_top_universities(student_data=None):
    """
    Analyzes and recommends universities using Mixtral LLM based on scraped data and student profile.
    
    Args:
        student_data (dict, optional): Student profile data. If None, loads from student_data.json
        
    Returns:
        pd.DataFrame: DataFrame containing top 5 university recommendations with details
    """
    try:
        # Load student data if not provided
        if student_data is None:
            try:
                student_data_path = os.path.join(os.getcwd(), 'student_data.json')
                with open(student_data_path, 'r') as f:
                    data = json.load(f)
                    # Get the first student's data
                    if 'students' in data and data['students']:
                        student_data = next(iter(data['students'].values()))
                        logging.info(f"Loaded student data: {student_data}")
                    else:
                        st.error("❌ No student data found in the file.")
                        return None
            except FileNotFoundError:
                st.error("❌ Student data not found. Please complete your profile first.")
                return None
            except json.JSONDecodeError:
                st.error("❌ Invalid student data format. Please complete your profile again.")
                return None
            except Exception as e:
                st.error(f"❌ Error loading student data: {str(e)}")
                logging.error(f"Error loading student data: {str(e)}", exc_info=True)
                return None
        
        # Validate required fields
        required_fields = ['interested_field_for_masters', 'preferred_countries']
        missing_fields = [field for field in required_fields if not student_data.get(field)]
        if missing_fields:
            st.error(f"❌ Missing required profile information: {', '.join(missing_fields)}")
            return None
            
        st.write("🔍 Analyzing your profile and university data...")
        
        # Load university data from scraping_results directory
        scraping_dir = os.path.join(os.getcwd(), 'scraping_results')
        if not os.path.exists(scraping_dir):
            st.error("❌ No university data found. Please run the university search and processing first.")
            return None
            
        # Load all university data
        university_data = []
        for filename in os.listdir(scraping_dir):
            if filename.endswith('_details.csv'):
                file_path = os.path.join(scraping_dir, filename)
                try:
                    # Read CSV and convert to dictionary
                    with open(file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        data = {row['key']: row['value'] for row in reader}
                        university_data.append(data)
                except Exception as e:
                    logging.error(f"Error reading {filename}: {str(e)}")
                    continue
        
        if not university_data:
            st.error("❌ No processed university data found. Please run the university processing first.")
            return None
            
        # Create prompt for LLM
        prompt = f"""
        Analyze the following student profile and university data to recommend the top 5 best-fitting universities.
        
        Student Profile:
        - Field of Interest: {student_data['interested_field_for_masters']}
        - Preferred Countries: {', '.join(student_data['preferred_countries'])}
        - Academic Background: 
          * BTech Branch: {student_data.get('btech_branch', 'Not specified')}
          * BTech CGPA: {student_data.get('btech_cgpa', 'Not specified')}
          * 12th Marks: {student_data.get('marks_12th', 'Not specified')}
          * 10th Marks: {student_data.get('marks_10th', 'Not specified')}
        - Test Scores:
          * IELTS: {student_data.get('ielts_score', 'Not specified')}
          * TOEFL: {student_data.get('toefl_score', 'Not specified')}
        - Work Experience: {student_data.get('work_experience', 'Not specified')}
        
        Available Universities:
        {json.dumps(university_data, indent=2)}
        
        Consider these factors:
        1. Academic alignment with student's field ({student_data['interested_field_for_masters']})
        2. Location preferences ({', '.join(student_data['preferred_countries'])})
        3. Program quality and reputation
        4. Research opportunities
        5. Career prospects
        6. Admission requirements vs student's scores:
           - BTech CGPA: {student_data.get('btech_cgpa', 'Not specified')}
           - IELTS: {student_data.get('ielts_score', 'Not specified')}
           - TOEFL: {student_data.get('toefl_score', 'Not specified')}
        7. Work experience relevance: {student_data.get('work_experience', 'Not specified')}
        8. Application deadlines
        9. Scholarship opportunities
        
        Provide specific recommendations with:
        1. Clear explanation of program fit
        2. Analysis of admission chances based on scores
        3. Specific strengths of each recommended program
        4. Action items for application
        """
        
        # Call LLM for recommendations
        try:
            recommendations = query_llm(prompt)
            
            # Create a DataFrame for display
            df_data = []
            for rec in recommendations['recommendations']:
                df_data.append({
                    'Rank': rec['rank'],
                    'University': rec['university_name'],
                    'Program': rec['program_name'],
                    'Fit Score': f"{rec['fit_score']}/100",
                    'Key Strengths': ', '.join(rec['key_strengths']),
                    'Admission Chances': rec['admission_chances']
                })
                
            recommendations_df = pd.DataFrame(df_data)
            
            # Display detailed information
            st.markdown("### 🎓 Detailed Analysis")
            st.markdown(f"**Overall Summary:**\n{recommendations['analysis_summary']}")
            
            st.markdown("### 📊 University Details")
            for rec in recommendations['recommendations']:
                with st.expander(f"#{rec['rank']} - {rec['university_name']}"):
                    st.markdown(f"""
                    * **Program:** {rec['program_name']}
                    * **Fit Score:** {rec['fit_score']}/100
                    * **Key Strengths:**
                      * {' * '.join(rec['key_strengths'])}
                    * **Program Alignment:** {rec['program_alignment']}
                    * **Admission Chances:** {rec['admission_chances']}
                    * **Financial Considerations:**
                      * Total Cost: {rec['financial_considerations']['total_cost']}
                      * Available Aid: {rec['financial_considerations']['available_aid']}
                      * ROI: {rec['financial_considerations']['roi_assessment']}
                    * **Next Steps:**
                      * {' * '.join(rec['action_items'])}
                    """)
            
            return recommendations_df
            
        except Exception as e:
            st.error(f"❌ Error generating recommendations: {str(e)}")
            logging.error(f"Error in LLM recommendation: {str(e)}", exc_info=True)
            return None
        
    except Exception as e:
        st.error(f"❌ An error occurred while generating recommendations: {str(e)}")
        logging.error(f"Error in recommend_top_universities: {str(e)}", exc_info=True)
        return None
