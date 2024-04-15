from bs4 import BeautifulSoup
    
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

def parse(content:str)->str:
  # If we cannot parse the content, return empty string.
  if not _is_valid_html(content):
    print(f'Not a valid HTML document:{content.text}\n')
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
          results.append(text+" \n")

  # Get the updated HTML with only title and body
  return " \n".join(results)

  
