from src.utils import load_sample_data
from src.models import VisaInfo
from typing import List, Optional
import logging
import os

def fetch_visa_info(country: str) -> Optional[VisaInfo]:
  """
  Fetches visa information for a given country.

  Args:
    country: The name of the country for which to fetch visa information.

  Returns:
    A VisaInfo object containing visa details, or None if not found.
  """
  try:
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'visa_info.json')
    visa_data = load_sample_data(file_path)
    for v in visa_data:
      if v['country'] == country:
        return VisaInfo(**v)
    logging.warning(f"Visa information not found for country: {country}")
    return None
  except Exception as e:
     logging.error(f"Error fetching visa information for {country}: {e}")
     return None