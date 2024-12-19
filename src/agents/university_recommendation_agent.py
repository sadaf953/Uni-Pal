import os
import csv
from typing import List, Dict
from googleapiclient.discovery import build
from src.config import settings
from src.models import StudentInfo, University
from src.utils import safe_log, extract_content_with_ai, search_web, convert_currency
from typing import Annotated, Dict
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd
import re


def google_search(search_query: str, api_key: str, num_results: int = 10) -> List[str]:
    """
    Performs a Google Search and returns a list of URLs.

    Args:
        search_query (str): The search query string.
        api_key (str): The Google Search API key.
        num_results (int): The number of results to return.

    Returns:
        List[str]: A list of URLs from the search results.
    """
    try:
        service = build("customsearch", "v1", developerKey=api_key)
        cse = service.cse()
        res = (
            cse.list(q=search_query, cx=settings.google_cse_id, num=num_results).execute()
        )
        urls = [item["link"] for item in res.get("items", [])]
        return urls
    except Exception as e:
        safe_log(f"Error during google search : {e}")
        return []


def save_universities_to_csv(universities: Dict[str, List[str]], filename: str = "data/Universities.csv") -> None:
    """
    Saves the list of university URLs to a CSV file.

    Args:
        universities (Dict[str, List[str]]): A dictionary of countries to lists of URLs.
        filename (str): The path to the CSV file.
    """
    try:
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["country", "url"])
            for country, urls in universities.items():
                for url in urls:
                    writer.writerow([country, url])
        safe_log(f"Successfully saved universities to {filename}")
    except Exception as e:
        safe_log(f"Error saving to CSV: {e}")


def setup_selenium_driver():
    """Sets up the Selenium WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-default-apps")
    
    # Add the binary location if it exists in the path
    chrome_binary_path = os.getenv("CHROME_BINARY_PATH")
    if chrome_binary_path:
         chrome_options.binary_location = chrome_binary_path


    service = ChromeService(executable_path=os.getenv("CHROME_DRIVER_PATH"))

    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def university_search_agent(state: Dict) -> Annotated[Dict, "university_search_agent"]:
    """
    Performs a Google search for universities based on student preferences, scrapes course details, and saves the information in the state.
    Args:
      state (Dict): The current state of the application, including the student's information.
    Returns:
      Dict: The updated state with a list of universities for each country
    """
    student_info = state["student_info"]
    if not isinstance(student_info, StudentInfo):
        safe_log(f"Expected StudentInfo, got: {type(student_info)}")
        return state

    if not student_info.preferred_countries:
        safe_log("No preferred countries found.")
        return state

    if not student_info.interested_field_for_masters:
        safe_log("No interested field for masters found.")
        return state

    universities = {}
    for country in student_info.preferred_countries:
        search_query = f"{country} universities for {student_info.interested_field_for_masters}"
        api_key = settings.google_api_key
        urls = google_search(search_query, api_key)
        universities[country] = urls
    save_universities_to_csv(universities)

    all_universities_data = []
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'Universities.csv')

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
       safe_log(f"Error loading universities from csv file {e}")
       return state
    
    driver = setup_selenium_driver()
    for index, row in df.iterrows():
            university_name = row['url'].split("/")[2]
            course_url = row['url']
            
            safe_log(f"Course url found for {university_name}: {course_url}")
            if not course_url:
                safe_log(f"No course URL found for {university_name}")
                continue

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
            
            try:
                safe_log(f"Scraping {course_url} for {university_name}")
                driver.get(course_url)
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # Wait for the body to load
                html = driver.page_source
                safe_log(f"Extracting details using LLM for {university_name}")
                llm_response = extract_content_with_ai(html, llm_prompt)

                if not llm_response or not llm_response.get('extracted_content'):
                    safe_log(f"No LLM response for {university_name}")
                    continue
                
                extracted_content = llm_response.get('extracted_content', {})
                if isinstance(extracted_content, dict):
                  if "tuition_fees" in extracted_content and isinstance(extracted_content["tuition_fees"],str):
                        currency_match = re.search(r'([A-Z]{3})', extracted_content["tuition_fees"])
                        if currency_match:
                            currency = currency_match.group(1)
                            amount_match = re.search(r'([\d\.]+)', extracted_content["tuition_fees"])
                            if amount_match:
                              amount = float(amount_match.group(1))
                              tuition_fees_inr = convert_currency(amount, currency, 'INR')
                              currency = "INR"
                            else:
                                safe_log(f"Could not parse amount for  {university_name}")
                                tuition_fees_inr = "N/A"
                        else:
                             safe_log(f"Could not parse currency for  {university_name}")
                             tuition_fees_inr = "N/A"
                  else:
                    tuition_fees_inr = "N/A"
                    currency = "N/A"

                  university_data = University(
                    name = extracted_content.get('university_name', "N/A"),
                    url = course_url,
                    currency = currency,
                    tuition_fees = str(tuition_fees_inr) if tuition_fees_inr != "N/A" else "N/A",
                    eligibility_criteria = extracted_content.get('eligibility_criteria', "N/A"),
                    deadlines = extracted_content.get('deadlines', "N/A"),
                    course_curriculum = extracted_content.get('course_curriculum', "N/A"),
                    scholarship_options = extracted_content.get('scholarship_options', "N/A")
                  )
                  all_universities_data.append(university_data)
                else:
                    safe_log(f"LLM did not return a dict for  {university_name}, instead returned {extracted_content}")

            except TimeoutException:
                 safe_log(f"Timeout scraping {course_url} for {university_name}")
                 continue
            except Exception as e:
                 safe_log(f"Error scraping {course_url} for {university_name} : {e}")
                 continue
    driver.quit() # Quit selenium driver

    # Update the state
    updated_student_info = student_info.copy(update={"university_details": all_universities_data})
    state["student_info"] = updated_student_info
    
    return state