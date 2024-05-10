from bs4 import BeautifulSoup
import PyPDF2
import requests
from io import BytesIO
from applog import logger as logging

def _is_valid_pdf(url:str)->bool:
  """Check if the URL points to a PDF file."""
  # Make a HEAD request to check the content type
  response = requests.head(url, allow_redirects=True)
  content_type = response.headers.get('Content-Type', '')
  
  # Check if the content type is PDF.
  if 'application/pdf' in content_type:
    return True
  return False

def _read_pdf(url:str)->str:
  # Make a GET request to download the PDF
  response = requests.get(url)
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

def parse(url:str)->str:
  if _is_valid_pdf(url):
    return _read_pdf(url)

  content = requests.get(url)
  content.encoding = 'utf-8'  # Ensures response.text is treated as UTF-8
  # If we cannot parse the content, return empty string.
  if not _is_valid_html(content):
    logging.warning(f'Not a valid HTML document:{content}\n')
    return ""

  results = []
  # Parse the HTML
  soup = BeautifulSoup(content.text, 'html.parser')
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

  
