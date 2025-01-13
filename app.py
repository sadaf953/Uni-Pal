import json
import os
import pandas as pd
import streamlit as st

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

def main():
    st.title("Top University Recommendations")

    # Load student data
    try:
        with open('student_data.json', 'r') as f:
            student_data = json.load(f)
    except FileNotFoundError:
        st.error("Student data file not found.")
        return

    # Get recommendations
    recommendations = recommend_top_universities(student_data)

    # Display recommendations
    if not recommendations.empty:
        st.subheader("Recommended Universities")
        st.dataframe(recommendations)
    else:
        st.info("No suitable universities found based on the data.")

if __name__ == "__main__":
    main()