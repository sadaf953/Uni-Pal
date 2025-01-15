import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Custom Search API settings
API_KEY = os.getenv('GOOGLE_API_KEY')
CX_CODE = os.getenv('GOOGLE_CX_CODE')

# LLM settings
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq')
