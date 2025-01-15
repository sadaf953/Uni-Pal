# test_llm_interface.py

import requests
import logging
from dotenv import load_dotenv
from src.llm_interface import query_llm

# Load environment variables
load_dotenv()

def test_query_llm():
    test_prompt = "What are the best universities for artificial intelligence?"
    
    # Simulate Gemini failure
    try:
        response = query_llm(test_prompt)
        print("Response from LLM:", response)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_query_llm()
