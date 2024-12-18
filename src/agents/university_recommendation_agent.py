import pandas as pd
from src.models import University
from typing import List
from src.config import settings
from src.utils import convert_currency

def recommend_universities(student_info) -> List[University]:
    df = pd.read_csv("data/universities.csv")

    # Convert tuition fees to INR
    df["tuition_fees_inr"] = df.apply(lambda row: convert_currency(row['tuition_fees_usd'], 'USD', 'INR') if row['country'] == "USA" else (convert_currency(row['tuition_fees_usd'], 'GBP', 'INR') if row['country'] == 'UK' else convert_currency(row['tuition_fees_usd'], 'AUD', 'INR')), axis=1)

    df["score"] = 0
    for index, row in df.iterrows():
      score = 0
      if row["country"] in student_info.preferred_countries:
        score += 10
      if row['cgpa_requirement'] <= student_info.btech_cgpa:
        score += 10

      if student_info.ielts_score is not None and row['ielts_requirement'] is not None:
         if row["ielts_requirement"] <= student_info.ielts_score:
            score += 5
      if student_info.toefl_score is not None and row['toefl_requirement'] is not None:
        if row["toefl_requirement"] <= student_info.toefl_score:
           score += 5
      
      # Add score based on interested field for Masters if available
      if student_info.Interested_feild_for_Masters:
        # This would require adding a column in universities.csv for specialization/field
        # For now, we'll leave it as a placeholder
        score += 3

      df.loc[index, 'score'] = score

    df = df.sort_values(by="score", ascending=False)
    recommended_universities = df.head(5)
    universities = [
      University(
            name=row['university_name'],
             tuition_fees=row['tuition_fees_inr'],
             eligibility_criteria=f"B.Tech with {row['cgpa_requirement']} CGPA or above, IELTS {row['ielts_requirement'] if row['ielts_requirement'] else 'N/A'}+, TOEFL {row['toefl_requirement'] if row['toefl_requirement'] else 'N/A' }+"
        )
            for index, row in recommended_universities.iterrows()
     ]
    return universities