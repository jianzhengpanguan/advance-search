from bs4 import BeautifulSoup
import PyPDF2
from io import BytesIO
from applog import logger as logging
import requests
import urllib3
import ssl
import configparser
import asyncio
from pyppeteer import launch
import urllib3
from urllib3.exceptions import InsecureRequestWarning

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

def _bypass_javascript_blocker(url:str)->str:
  async def get_html(url):
    # Launch a headless browser with the manually downloaded Chromium.
    browser = await launch(
      executablePath=config["CHROMIUM"]["path"], 
      headless=True, 
      args=["--no-sandbox"]
    )
    page = await browser.newPage()

    # Disable JavaScript on this page
    await page.setJavaScriptEnabled(False)

    # Navigate to the URL
    await page.goto(url)

    # Get the HTML content
    html = await page.content()

    if page:
      await page.close()

    # Close the browser
    try:
      await browser.close()
    except Exception as e:
      logging.warning("Failed to close browser:", e)
    
    return html

  # The event loop executes async tasks and handles I/O. By default, it's associated with the main thread
  # Each thread needs its own event loop. Accessing the loop from a different thread (e.g., ThreadPoolExecutor) causes the error
  # The web parser is running in thread, so we need to create a new event loop.
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  content = loop.run_until_complete(get_html(url))
  
  return content
   

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


if __name__ == "__main__":
  url = "https://www.nytimes.com/2017/06/01/climate/trump-paris-climate-agreement.html"
  print(parse(url)[:20])
