"""
AI-based content extraction utilities for the university recommendation system.
"""

# Standard library imports
import logging
import time
from typing import Dict
from datetime import datetime

# Third-party imports
from langchain.schema import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from src.llm_interface import query_llm


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry_error_callback=lambda retry_state: {
        "extracted_content": "",
        "error": str(retry_state.outcome.exception())
    }
)
def extract_content_with_ai(html_content: str, user_request: str) -> Dict:
    """
    Extract relevant information from HTML content using AI.
    
    Args:
        html_content (str): Raw HTML content
        user_request (str): User's specific request for information extraction
        
    Returns:
        dict: Extracted information in structured format
    """
    if not html_content:
        return {"extracted_content": "", "error": "No content to analyze"}

    try:
        # Truncate content if too long
        max_chars = 12000
        content = html_content[:max_chars] if len(html_content) > max_chars else html_content
        
        # Create a focused prompt for the AI
        prompt = f"""
        Analyze this webpage content and extract ONLY the following information:
        {user_request}
        
        Content to analyze:
        {content}
        
        Format your response exactly like this:
        1. University Name: [name]
        2. Country: [country]
        3. Tuition Fees: [amount with currency]
        4. Eligibility Criteria: [CGPA, IELTS, TOEFL requirements]
        5. Deadlines: [application deadlines]
        6. Course Curriculum: [brief overview]
        7. Scholarship options: [available scholarships]
        
        If any information is not found, use 'N/A'.
        """
        
        time.sleep(1)  # Rate limiting
        response = query_llm(prompt)
        
        return {
            "extracted_content": response if response else "",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Error in AI extraction: {str(e)}")
        return {"extracted_content": "", "error": str(e)}
