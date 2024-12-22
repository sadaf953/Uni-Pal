import json
import os
import logging

def load_sample_data(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Error loading data from {file_path}: {e}")
        return None

def fetch_visa_info(country):
    """
    Fetch visa information for a specific country, assuming application from India.

    Args:
        country (str): The destination country for which to fetch visa information.

    Returns:
        VisaInfo: A VisaInfo object containing visa details, or None if not found.
    """
    try:
        file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'visa_requirements.json')
        visa_data = load_sample_data(file_path)

        if visa_data is None:
            logging.warning("No visa data found.")
            return None

        for item in visa_data:
            if item['country'] == country and item['application_from'] == "India":  # Added nationality check
                # Assuming VisaInfo is defined elsewhere and can handle the structure
                # If VisaInfo isn't defined, you can just return the 'item' dictionary
                return item
        logging.warning(f"Visa information not found for country: {country}")
        return None
    except Exception as e:
        logging.error(f"Error fetching visa info for {country}: {e}")
        return None

def visa_checker_page():
    st.title("Visa Requirement Checker")
    selected_country = st.selectbox("Select Destination Country", ["USA", "UK", "Australia"])
    if selected_country:
        visa_info = fetch_visa_info(selected_country)
        print(f"Visa info for {selected_country}: {visa_info}")  # Debug print

        if visa_info:
            st.subheader(f"Visa Information for {selected_country}")
            if 'visa_types' in visa_info:  # Check if 'visa_types' key exists
                for visa_type in visa_info['visa_types']:  # Access 'visa_types' as a dictionary key
                    print(f"Visa Type: {visa_type}") # Debug print inside the loop
                    st.write(f"**Visa Type:** {visa_type.get('type', 'N/A')}")
                    st.write(f"  - Processing Time: {visa_type.get('processing_time_months', {}).get('range', 'N/A')}")
                    if visa_type.get('financial_requirements'):
                        st.write(f"  - Financial Requirements:")
                        st.write(f"    - Bank Balance (Months): {visa_type['financial_requirements'].get('bank_balance_months', 'N/A')}")
                        if 'estimated_cost_of_attendance_usd' in visa_type['financial_requirements']:
                            st.write(f"    - Estimated Cost of Attendance (USD): {visa_type['financial_requirements']['estimated_cost_of_attendance_usd']}")
                        if 'monthly_living_costs_outside_london_gbp' in visa_type['financial_requirements']:
                            st.write(f"    - Monthly Living Costs (Outside London, GBP): {visa_type['financial_requirements']['monthly_living_costs_outside_london_gbp']}")
                        if 'annual_living_costs_aud' in visa_type['financial_requirements']:
                            st.write(f"    - Annual Living Costs (AUD): {visa_type['financial_requirements']['annual_living_costs_aud']}")
                        st.write(f"    - Proof of Funds Required: {'Yes' if visa_type['financial_requirements'].get('proof_of_funds_required') else 'No'}")
                    if visa_type.get('loan_process'):
                        st.write(f"  - Loan Process:")
                        st.write(f"    - Loan Acceptance Allowed: {'Yes' if visa_type['loan_process'].get('loan_acceptance_allowed') else 'No'}")
                        if visa_type['loan_process'].get('required_documents_summary'):
                            st.write(f"    - Required Documents (Summary):")
                            for doc in visa_type['loan_process']['required_documents_summary']:
                                st.write(f"      - {doc}")
                    if visa_type.get('additional_requirements'):
                        st.write(f"  - Additional Requirements:")
                        for req in visa_type['additional_requirements']:
                            st.write(f"    - {req}")
                    st.write("---")
            else:
                st.warning(f"No visa types information found for {selected_country}.")
        else:
            st.info(f"No specific visa information found for {selected_country} at the moment.")