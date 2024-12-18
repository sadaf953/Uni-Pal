from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup
from src.config import settings
import time
import json
from src.llm_interface import query_llm

def scrape_website_selenium(url: str, selector: str, parser='html.parser') -> str:
  chrome_options = Options()
  chrome_options.add_argument("--headless")
  chrome_service = ChromeService()
  driver = webdriver.Chrome(service=chrome_service, options=chrome_options)
  try:
    driver.get(url)
    wait = WebDriverWait(driver, 10)
    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    return element.get_attribute("innerHTML")
  except Exception as e:
    print(f"Error scraping {url}: {e}")
    return None
  finally:
      driver.quit()

def scrape_website(url: str, parser='html.parser'):
    """Scrape a website and return its content"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, parser)
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return None


def search_web(query: str) -> list:
    """Mock web search"""
    print(f"Mock Search query: {query}")
    return []

def convert_currency(amount: float, source_currency: str, target_currency: str) -> float:
    """Mock currency conversion (only convert USD to INR)"""
    print(f"Mock conversion {amount} {source_currency} to {target_currency}")
    if source_currency == 'USD' and target_currency == 'INR':
      return amount * 82
    if source_currency == 'GBP' and target_currency == 'INR':
      return amount * 103
    if source_currency == 'AUD' and target_currency == 'INR':
       return amount * 54
    return 0

def load_sample_data(file_path: str):
  try:
    with open(file_path, 'r') as f:
       return json.load(f)
  except Exception as e:
    print(f"Error loading {file_path}: {e}")
    return {}