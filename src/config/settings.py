import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
API_KEY = os.getenv('API_KEY')
CX_CODE = os.getenv('CX_CODE')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
SERP_API_KEY = os.getenv('SERP_API_KEY')

# Constants
MAX_RETRIES = 3
TIMEOUT = 30
TEMPERATURE = 0.1
