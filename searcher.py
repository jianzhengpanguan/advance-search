import requests
import re
import gpt
import configparser

_NUM_SEARCH_RESULT = 3

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config.ini')

# Given the search result, determine if the search result is relevant to my statement.
def _is_relevant(statement, search_result):
  prompt = f"""Given {search_result}, is that relevant to {statement}? Anwser in the following format:
  Yes/No
  """
  response = gpt.request(prompt)
  if 'No' in response:
    return False
  return True

# Given the search result, determine if additional search is needed.
def _is_enough(statement, search_result):
  prompt = f"""Given {search_result}, can you verify {statement}? Answer in the following format:
  Yes/No
  """
  response = gpt.request(prompt)
  if 'No' in response:
    return False
  return True

# Based on the searched result, let LLM define follow up search questions.
def _to_follow_up_searches(statement, search_result):
  prompt = f"""Given {search_result}, if I want to verify {statement}, what else should I search? Answer in the following format:
  Search:
  1. __
  2. __
  """
  suggest_search = gpt.request(prompt)
  follow_up = re.findall(r'\d+\.\s+(.*)', suggest_search)
  return follow_up

# Summerize the search result to save tokens.
def _summerize(text):
  prompt = f"""summerize {text}"""
  return gpt.request(prompt)

# Let LLM suggests the keywords for the search.
def _to_keywords(text):
  prompt = f"""If I want to search for: {text}, what keywords should I use? Answer in the following format:
  Keywords:
  1. __
  2. __
  """
  gpt_suggest = gpt.request(prompt)
  raw_keywords = re.findall(r'\d+\.\s+(.*)', gpt_suggest)
  keywords = []
  for suggest_keyword in raw_keywords:
    for keyword in suggest_keyword.split(' '):
      keywords.append(keyword.strip())
  return ' AND '.join(keywords)

def _web_request(search, keywords):
  url = f"{config['SEARCH']['url']}?key={config['SEARCH']['api_key']}&cx={config['SEARCH']['cx']}&searchTerms={keywords}&q={search}&num={_NUM_SEARCH_RESULT}"

  response = requests.get(url)
  data = response.json()
  output = []
  if 'items' not in data:
    print("query:", search, "got not result", data)
    return output
  for item in data['items']:
    if 'title' in item and 'snippet' in item and 'link' in item:
      if _is_relevant(search, item['title'] + item['snippet']):
        output.append(item['title'] + item['snippet'] + item['link'])
  return output

def search(statement, max_iter):
  init_keywords = _to_keywords(statement)
  results = []
  for _ in range(max_iter):
    summerized_result = ''
    if results:
      summerized_result = _summerize(results)

    # Check if the current fact is enough.
    if _is_enough(statement, summerized_result):
      return results

    searches = _to_follow_up_searches(statement, summerized_result)
    for search in searches:
        keywords = init_keywords+_to_keywords(search)
        results.extend(_web_request(search, keywords))
  return results