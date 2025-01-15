import os
from dotenv import load_dotenv
import logging

load_dotenv()

class Settings:
    """
    Configuration settings for the UniPal application.
    """

    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
    SERP_API_KEY = os.getenv("SERP_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # Required for Mixtral API
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Add this for Gemini
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'unipal.db'))}")
    DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq") # set groq as default LLM, use 'ollama' for local ollama
    LLM_MODEL = os.getenv("LLM_MODEL", "mixtral-8x7b-32768") #set default model
    TAVILY_API_KEY=os.getenv("TRAVILY_API_KEY")
    API_KEY = os.getenv("API_KEY")
    CX_CODE = os.getenv("CX_CODE")
    MAX_SEARCH_RESULTS = 30
    SEARCH_TIMEOUT = 30
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    SCRAPING_DIR = os.path.join(BASE_DIR, "scraping_results")
    UNIVERSITY_CSV = "university.csv"
    PROCESSED_CSV = "processed_universities.csv"
    STUDENT_DATA_JSON = "student_data.json"
    LOG_LEVEL = "INFO"
    LOG_FILE = os.path.join(BASE_DIR, "app.log")

    def __init__(self):
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.SCRAPING_DIR, exist_ok=True)
        logging.info(f"Loaded environment variables: {os.environ}")
        logging.info(f"GROQ_API_KEY is: {self.GROQ_API_KEY}")
        logging.info(f"GOOGLE_API_KEY is: {self.GOOGLE_API_KEY}")  # Add logging for Google API key
        logging.info(f"LLM_PROVIDER is: {self.LLM_PROVIDER}")
        logging.info(f"TRAVILY_API_KEY is: {self.TAVILY_API_KEY}")
        logging.info(f"API_KEY is: {self.API_KEY}")
        logging.info(f"CX_CODE is: {self.CX_CODE}")

settings = Settings()
