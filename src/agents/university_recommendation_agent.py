import pandas as pd
from typing import List, Dict, Annotated  # Ensure List is imported
from src.models import StudentInfo, University
from src.utils import safe_log, extract_content_with_ai, convert_currency
import requests  # Import the requests library
import logging
# Other imports...

def save_universities_to_csv(universities: List[University], filename: str = "data/universities.csv") -> None:
    """
    Saves the list of universities to a CSV file.

    Args:
        universities: List of University objects to save.
        filename: The name of the file to save the universities to.
    """
    data = []
    for university in universities:
        data.append({
            "name": university.name,
            "url": university.url,
            "currency": university.currency,
            "tuition_fees": university.tuition_fees,
            "eligibility_criteria": university.eligibility_criteria,
            "deadlines": university.deadlines,
            "course_curriculum": university.course_curriculum,
            "scholarship_options": university.scholarship_options
        })

    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)