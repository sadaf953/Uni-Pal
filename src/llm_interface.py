import os
import logging
import json
import requests
from dotenv import load_dotenv
from src.config import settings

# Load environment variables
load_dotenv()

def query_llm(prompt, temperature=0.1, max_tokens=1024):
    """
    Query the LLMs via their respective APIs with fallback options.
    
    Args:
        prompt (str): The input prompt for the LLM
        temperature (float, optional): Sampling temperature. Defaults to 0.1.
        max_tokens (int, optional): Maximum number of tokens to generate. Defaults to 1024.
    
    Returns:
        dict: The parsed JSON response from the LLM
    """
    try:
        # Attempt to query Gemini
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gemini-pro",
                "messages": [
                    {"role": "system", "content": "You are a university recommendation expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Gemini API error: {str(e)}")

        # Attempt to query Mixtral
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": "You are a university recommendation expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Mixtral API error: {str(e)}")

        # Attempt to query Llama
        try:
            url = "https://api.llama.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.LLAMA_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-2",
                "messages": [
                    {"role": "system", "content": "You are a university recommendation expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Llama API error: {str(e)}")
            raise ValueError("All LLMs failed to generate a response.")
    except Exception as e:
        logging.error(f"Error in query_llm: {str(e)}", exc_info=True)
        raise e

def create_prompt(prompt: str):
    """
    Creates a prompt string.
    """
    return f"{prompt}"

def get_university_urls_with_llm(course: str, country: str, count: int = 30):
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
    try:
        prompt = f"""Find {count} universities in {country} that offer {course} programs. Return ONLY a JSON array of objects with 'name', 'url', and 'country' fields. Example format:
        [
            {{"name": "University Name", "url": "https://university.edu", "country": "{country}"}}
        ]
        """
        
        response = query_llm(prompt)
        if isinstance(response, str):
            response = json.loads(response)
            
        return response[:count]
        
    except Exception as e:
        logging.error(f"Error in get_university_urls_with_llm: {str(e)}")
        return []

if __name__ == "__main__":
    print("Starting LLM test...")