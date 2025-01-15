import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai
from src.config import settings
import datetime
import json

# Load environment variables
load_dotenv()

# Configure Google AI
genai.configure(api_key=settings.GOOGLE_API_KEY)

class LLMs:
    def __init__(self):
        # Initialize Gemini model
        self.model = genai.GenerativeModel('gemini-pro')

model = LLMs()
Gemini_Exp1206 = model.model

def query_llm(prompt, model_name="gemini-pro", temperature=0.1, max_tokens=1024):
    """
    Query the LLM with a given prompt.
    
    Args:
        prompt (str): The input prompt for the LLM
        model_name (str, optional): Name of the model to use. Defaults to "gemini-pro".
        temperature (float, optional): Sampling temperature. Defaults to 0.1.
        max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 1024.
    
    Returns:
        str: The generated response from the LLM
    """
    try:
        # Configure the model
        model = genai.GenerativeModel(model_name)
        
        # Generate response with error handling
        generation_config = {
            'temperature': temperature,
            'max_output_tokens': max_tokens,
            'top_p': 1,
            'top_k': 1,
            'stop_sequences': ["---END---"]
        }
        
        # Create a more structured prompt
        structured_prompt = f"""
        Task: University Recommendation Analysis
        
        Instructions:
        - Analyze the provided information carefully
        - Generate recommendations in JSON format
        - Be specific and detailed in your analysis
        - Ensure all required fields are present
        - Return ONLY valid JSON, no other text
        
        Input:
        {prompt}
        
        Response format:
        {{
            "recommendations": [
                {{
                    "rank": 1,
                    "university_name": "University Name",
                    "program_name": "Program Name",
                    "fit_score": 85,
                    "key_strengths": ["strength1", "strength2"],
                    "program_alignment": "Program alignment details",
                    "admission_chances": "High/Medium/Low",
                    "financial_considerations": {{
                        "total_cost": "Estimated total cost",
                        "available_aid": "Available aid options",
                        "roi_assessment": "ROI assessment"
                    }},
                    "action_items": ["action1", "action2"]
                }}
            ],
            "analysis_summary": "Overall analysis summary"
        }}
        
        Remember: Return ONLY the JSON object, no other text.
        """
        
        # Attempt to generate response
        response = model.generate_content(
            structured_prompt,
            generation_config=generation_config,
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                },
            ]
        )
        
        # Check for safety issues or generation problems
        if not response.parts:
            logging.error("No response generated")
            raise ValueError("No response generated from the LLM")
        
        # Extract and clean the response text
        response_text = response.text.strip()
        
        # Log the response for debugging
        logging.debug(f"Raw LLM Response: {response_text}")
        
        try:
            response_json = json.loads(response_text)
            return response_json
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response: {str(e)}")
            raise ValueError("Invalid JSON response from the LLM")
        
    except Exception as e:
        logging.error(f"Error in query_llm: {str(e)}", exc_info=True)
        raise e

def testing_llms():
    parser = None
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"llm_test_results_{timestamp}.md"
    
    with open(output_file, "w") as f:
        f.write(f"# LLM Testing Results - {timestamp}\n\n")
        model_name = "Gemini_Exp1206"
        f.write(f"## {model_name}\n\n")
        messages = [
            "Reply only in 30 words",
            "explain a random topic from philosophy",
        ]

        try:
            result = query_llm(messages[1], model_name="gemini-pro")
            f.write(f"**Response:**\n\n{json.dumps(result, indent=4)}\n\n")

        except Exception as e:
            f.write(f"**Error:**\n\n```\n{str(e)}\n```\n\n")
    
    print(f"Results have been saved to {output_file}")

def create_prompt(prompt: str) -> str:
    """
    Creates a prompt string.
    """
    return prompt


def get_university_urls_with_llm(course: str, country: str, count: int = 30) -> list[dict[str, str]]:
    """
    Uses LLM to find university URLs for a specific course and country.

    Args:
        course (str): The course to search for
        country (str): The country to search in
        count (int): Number of universities to find (default: 30)

    Returns:
        List[Dict[str, str]]: List of dictionaries containing university info
            Each dict has keys: 'name', 'url', 'country'
    """
    results = []
    
    # Create a more structured prompt for the LLM
    prompt = f"""Task: Find {count} universities in {country} that offer {course} programs.

Please provide a list of universities in the following format:
1. University Name: [Full Official Name]
   Program URL: [Exact URL of the {course} program page]

Requirements:
- Only include accredited universities
- URLs must be direct links to the {course} program or department
- Focus on universities known to have strong {course} programs
- Include both public and private universities
- Verify each URL exists before including it

Example format:
1. Massachusetts Institute of Technology
   Program URL: https://www.eecs.mit.edu/academics/graduate-programs/

Please provide {count} universities following this exact format."""
    
    try:
        # Add debug logging
        logging.info(f"Querying LLM for {course} programs in {country}")
        
        response = query_llm(prompt, model_name="gemini-pro")
        
        # Add debug logging
        logging.info(f"LLM Response received: {response[:200]}...")
        
        # Process the response to extract universities and URLs
        # Look for numbered entries like "1.", "2.", etc.
        entries = response.split('\n\n')
        
        for entry in entries:
            if not entry.strip():
                continue
                
            # Look for program URL in the entry
            url_match = None
            for line in entry.split('\n'):
                if line.strip().startswith('Program URL:'):
                    url_match = line.strip().replace('Program URL:', '').strip()
                    break
            if url_match:
                url = url_match
                
                # Extract university name (text before "Program URL" or http)
                name_match = None
                for line in entry.split('\n'):
                    if line.strip().startswith('University Name:'):
                        name_match = line.strip().replace('University Name:', '').strip()
                        break
                if name_match:
                    name = name_match
                    if name and url:  # Only add if we have both name and URL
                        results.append({
                            'name': name,
                            'url': url,
                            'country': country
                        })
                        logging.info(f"Found university: {name} with URL: {url}")
                
            if len(results) >= count:
                break
                    
        if not results:
            logging.warning("No universities found in LLM response")
            
        logging.info(f"Found {len(results)} universities with program URLs")
        return results
        
    except Exception as e:
        logging.error(f"Error in LLM university search: {str(e)}")
        logging.error(f"Full error: {str(e.__class__.__name__)}: {str(e)}")
        return []


if __name__ == "__main__":
    print("Starting Groq test...")
    # test_groq_directly()
    print("Test complete.")