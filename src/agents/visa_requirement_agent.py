from src.utils import load_sample_data
from src.models import VisaInfo
from typing import List
def fetch_visa_info(country: str) -> VisaInfo:
  visa_data = load_sample_data("data/visa_info.json")
  for v in visa_data:
    if v['country'] == country:
      return VisaInfo(**v)
  return None