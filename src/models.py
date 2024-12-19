from pydantic import BaseModel
from typing import List, Optional

class StudentInfo(BaseModel):
    """
    Model for student information.
    """
    name: str
    contact_info: str
    marks_10th: int
    marks_12th: int
    btech_cgpa: float
    ielts_score: Optional[float] = None
    toefl_score: Optional[float] = None
    work_experience: Optional[str] = None
    preferred_countries: List[str]
    btech_branch: str
    interested_field_for_masters: Optional[str] = None


class University(BaseModel):
    """
    Model for university information.
    """
    name: str
    url: str
    ranking: Optional[int]
    tuition_fees: Optional[str]
    currency: Optional[str]
    eligibility_criteria: Optional[str]
    deadlines: Optional[str]
    course_curriculum: Optional[str] = None
    scholarship_options: Optional[str] = None


class VisaInfo(BaseModel):
    """
    Model for visa information.
    """
    country: str
    requirements: List[str]
    fees: str
    currency: str

class ScholarshipInfo(BaseModel):
  """
  Model for scholarship information.
  """
  name: str
  description: str
  eligibility: str
  amount: str

class Document(BaseModel):
    """
    Model for application documents
    """
    id: int
    name: str
    status: str  # pending, in_progress, completed
    description: Optional[str] = None
    required: bool = True