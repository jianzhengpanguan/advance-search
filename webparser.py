from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO
from applog import logger as logging
import requests
import urllib3
import ssl
import concurrent.futures
import configparser
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Suppress only the InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')

class CustomHttpAdapter(requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session


def _bypass_javascript_blocker(url: str) -> str:
    # Configure Selenium to use the local Chromium browser and ChromeDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    # Disable JavaScript
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.javascript": 2})
    chrome_options.add_argument("--log-level=3")

    # Initialize WebDriver
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    try:
      # Navigate to the URL
      driver.get(url)

      # Get the HTML content
      html = driver.page_source
    finally:
      # Clean up: close the browser
      driver.quit()

    return html
   

def _is_valid_pdf(url:str)->bool:
  """Check if the URL points to a PDF file."""
  # Make a HEAD request to check the content type
  try:
    response = requests.head(url, allow_redirects=True)
  except requests.exceptions.SSLError as e:
    logging.warning(f"Request PDF has SSL Error: {e}")
    # Make a request ignoring SSL certificate verification
    try:
      response = get_legacy_session().head(url, allow_redirects=True)
    except requests.exceptions.SSLError as e:
      response = requests.get(url, allow_redirects=True, verify=False)

  content_type = response.headers.get('Content-Type', '')
  
  # Check if the content type is PDF.
  if 'application/pdf' in content_type:
    return True
  return False

def _read_pdf(url:str)->str:
  # Make a GET request to download the PDF
  try:
    response = requests.get(url, allow_redirects=True)
  except requests.exceptions.SSLError as e:
    logging.warning(f"Request PDF has SSL Error: {e}")
    # Make a request ignoring SSL certificate verification
    try:
      response = get_legacy_session().get(url, allow_redirects=True)
    except requests.exceptions.SSLError as e:
      response = requests.get(url, allow_redirects=True, verify=False)
  response.encoding = 'utf-8'  # Ensures response.text is treated as UTF-8
  try:
    response.raise_for_status()  # Raise an exception for bad requests
  except requests.RequestException as e:
    logging.error(f"Failed to request: {str(e)}")
    return ""

  # Use BytesIO to handle the PDF from memory
  with BytesIO(response.content) as pdf_file:
    try:
      pdf_reader = PyPDF2.PdfReader(pdf_file)
    except PyPDF2.errors.PdfReadError as e:
      logging.error(f"Failed to read PDF: {str(e)}")
      return ""

    texts = []
    # Extract text from each page
    for page in pdf_reader.pages:
      texts.append(page.extract_text())
    return "\n".join(filter(None, texts))  # Join and filter out None values

    
def _is_valid_html(content):
  """Check if the response is a valid HTML document."""
  # Check Content-Type
  content_type = content.headers.get('Content-Type', '')
  if 'html' not in content_type:
      return False

  # Check Status Code
  if content.status_code != 200:
      return False

  # Attempt to parse HTML
  try:
      BeautifulSoup(content.text, 'html.parser')
  except Exception:
      return False

  return True

def _read_html(url):
  try:
    response = requests.get(url, allow_redirects=True)
  except requests.exceptions.SSLError as e:
    logging.warning(f"Request PDF has SSL Error: {e}")
    # Make a request ignoring SSL certificate verification
    try:
      response = get_legacy_session().get(url, allow_redirects=True)
    except requests.exceptions.SSLError as e:
      response = requests.get(url, allow_redirects=True, verify=False)

  raw_html = response.text
  # If we cannot parse the content, return empty string.
  if not _is_valid_html(response):
    logging.warning(f'Not a valid HTML document:{response}\n')
    # Try to bypass the JavaScript blocker and fetch the html again.
    raw_html = _bypass_javascript_blocker(url)

  results = []
  # Parse the HTML
  soup = BeautifulSoup(raw_html, 'html.parser')
  # Extract the title and body.
  title = soup.title
  if title:
    results.append(title.get_text(strip=True))

  # Define the tags of interest.
  tags_of_interest = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div']

  # Extract text from the tags of interest
  if soup.body:
    for tag in tags_of_interest:
      for element in soup.body.find_all(tag):
        text = element.get_text(strip=True)
        if text:
          results.append(text+"\n")

  # Get the updated HTML with only title and body
  return " \n".join(results)

def parse(url:str)->str:
  if _is_valid_pdf(url):
    return _read_pdf(url)
  return _read_html(url)
