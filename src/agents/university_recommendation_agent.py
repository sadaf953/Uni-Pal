import pandas as pd
from src.models import University
from typing import List, Dict, Any
from src.config import settings
from src.utils import convert_currency, search_web, scrape_website, extract_content_with_ai
import logging
import os
import csv
from langchain.schema import HumanMessage, SystemMessage

def recommend_universities(student_info) -> List[University]:
    """
    Recommends universities based on student information.

    Args:
      student_info: An object of type StudentInfo containing student details.

    Returns:
      A list of University objects representing the top recommended universities.
    """
    logging.info("Starting recommend_universities")
    preferred_countries = student_info.preferred_countries
    interested_field = student_info.interested_field_for_masters
    if not preferred_countries or not interested_field:
        logging.error("Preferred countries or interested field is missing")
        return []

    all_universities_data = []
    for country in preferred_countries:
        query = f"{country} universities for {interested_field}"
        logging.info(f"Searching for: {query}")
        search_results = search_web(query)
        if not search_results:
            logging.warning(f"No search results for {query}")
            continue

        for result in search_results:
            university_name = result.get('title', 'N/A').split('|')[0].strip() if result.get('title') else "N/A"
            url = result.get('link', 'N/A')
            logging.info(f"University name: {university_name} url: {url}")
            if url == 'N/A':
                logging.warning(f"No URL found for {university_name}")
                continue

            search_url_result = search_web(f"{university_name} {interested_field} course page")
            if not search_url_result or not search_url_result[0].get('link'):
                logging.warning(f"No course page found for {university_name}")
                continue

            course_url = search_url_result[0].get('link')
            logging.info(f"Course url found for {university_name}: {course_url}")
            if not course_url:
                logging.warning(f"No course URL found for {university_name}")
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
            logging.info(f"Scraping {course_url} for {university_name}")
            html = scrape_website(course_url)

            if not html:
                logging.warning(f"Could not scrape page for {university_name}")
                continue
            logging.info(f"Extracting details using LLM for {university_name}")
            llm_response = extract_content_with_ai(html, llm_prompt)

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

                all_universities_data.append({
                    "university_name": university_name_llm,
                    "university_url": course_url,
                    "country": country,
                    "tuition_fees_usd": tuition_fees,
                    "cgpa_requirement": eligibility_criteria,
                    "deadlines": deadlines,
                    "course_curriculum": course_curriculum,
                    "scholarship_options": scholarship_options
                })
            except Exception as e:
                logging.error(f"Error parsing LLM output for {university_name}: {e}")

    if not all_universities_data:
        logging.warning("No university data found")
        return []

    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'universities.csv')
    logging.info(f"Writing to file: {file_path}")

    # Write the data to the csv file
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=all_universities_data[0].keys())
        writer.writeheader()
        writer.writerows(all_universities_data)

    df = pd.read_csv(file_path)

    # Convert tuition fees to INR
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
        return convert_currency(row['tuition_fees_usd'], row['currency'], 'INR')

    df["tuition_fees_inr"] = df.apply(convert_fees, axis=1)

    df["score"] = 0
    for index, row in df.iterrows():
        score = 0
        if row["country"] in student_info.preferred_countries:
            score += 10
        if 'cgpa_requirement' in row and isinstance(row['cgpa_requirement'], str):
            try:
                cgpa = float(row['cgpa_requirement'].split("CGPA")[0].strip().split("with")[-1].strip())
                if cgpa <= student_info.btech_cgpa:
                    score += 10
            except:
                logging.warning(f"Could not parse cgpa requirement for {row['university_name']}")
        if 'ielts_requirement' in row and isinstance(row['ielts_requirement'], str):
            try:
                ielts = float(row['ielts_requirement'].split("+")[0].strip())
                if student_info.ielts_score is not None and ielts <= student_info.ielts_score:
                    score += 5
            except:
                logging.warning(f"Could not parse ielts requirement for {row['university_name']}")

        if 'toefl_requirement' in row and isinstance(row['toefl_requirement'], str):
            try:
                toefl = float(row['toefl_requirement'].split("+")[0].strip())
                if student_info.toefl_score is not None and toefl <= student_info.toefl_score:
                    score += 5
            except:
                logging.warning(f"Could not parse toefl requirement for {row['university_name']}")

        # Add score based on interested field for Masters if available
        if student_info.interested_field_for_masters:
            # This would require adding a column in universities.csv for specialization/field
            # For now, we'll leave it as a placeholder
            score += 3

        df.loc[index, 'score'] = score

    df = df.sort_values(by="score", ascending=False)
    recommended_universities = df.head(5)
    universities = [
        University(
            name=row['university_name'],
            url=row['university_url'],
            tuition_fees=str(row['tuition_fees_inr']) if row['tuition_fees_inr'] is not None else "N/A",
            currency='INR',
            eligibility_criteria=f"B.Tech with {row['cgpa_requirement']} CGPA or above, IELTS {row['ielts_requirement'] if 'ielts_requirement' in row else 'N/A'}+, TOEFL {row['toefl_requirement'] if 'toefl_requirement' in row else 'N/A'}+"
        )
        for index, row in recommended_universities.iterrows()
    ]
    logging.info(f"Returning {len(universities)} universities")
    return universities
