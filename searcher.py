import requests
import re
import gpt
import configparser
import webparser
import math
import logiclinker
import concurrent.futures

_NUM_SEARCH_RESULT = 3
_NUM_SEARCHES = 4
_CHUCK_SIZE = 500
_SUMMERIZED_SIZE = 100

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config.ini')

# Given the search result, determine if the search result is relevant to the statement.
def _is_relevant(statement, search_result):
  prompt = f"""
  Given `{search_result}`
  is that relevant to `{statement}`? 
  
  * Rephrase and expand the question
  * Think step by step (chain of thinking)
  * Answer the yes/no.

  Output in the following format:
  ```
  # Rephrased and expanded questions
  *__
  *__
  # Chain of thinking:
  *__
  *__
  # Answer:
  Yes/No
  ```
  """
  # We check multiple(e.g., 4 by default) searchs' results(e.g., by default top 3 result per search) multiple rounds(e.g., by default 3 iterations).
  # By default, we will request gpt 4 * 3 * 3 = 36 times per statement.
  # Use basic model to reduce cost.
  response = gpt.request(statement=prompt, provider_type=gpt.ProviderType.anthropic, model_type=gpt.ModelType.basic_model)
  try:
    answer = response.split("Answer")[-1]
  except IndexError:
    return False
  if 'Yes' in answer:
    return True
  return False

# Given the search result, determine if additional search is needed.
def _is_enough(statement, search_result):
  if not search_result:
    return False

  prompt = f"""
  Given `{search_result}`
  can you verify `{statement}`? 
  
  * Rephrase and expand the question
  * Think step by step (chain of thinking)
  * Answer the yes/no.

  Output in the following format:
  ```
  # Rephrased and expanded questions
  *__
  *__
  # Chain of thinking:
  *__
  *__
  # Answer:
  Yes/No
  ```
  """
  response = gpt.request(statement=prompt)
  answer = response.split("Answer")[-1]
  if 'Yes' in answer:
    return True
  return False

# Based on the searched result, let LLM define follow up search questions.
def _to_follow_up_searches(statement, search_result):
  prompt = f"""
  Given `{search_result}`
  if I want to verify `{statement}`
  what else should I search?

  * Rephrase and expand the question
  * Think step by step (chain of thinking)
  * List the searches by importance.

  Output in the following format:
  ```
  # Rephrased and expanded questions
  *__
  *__
  # Chain of thinking:
  *__
  *__
  # Search:
  1. __
  2. __
  ```
  """
  response = gpt.request(prompt)
  print("_to_follow_up_searches():", response)
  suggest_search = response.split("Search")[-1]
  follow_up = re.findall(r'\d+\.\s+(.*)', suggest_search)
  return follow_up[:_NUM_SEARCHES]

# Summerize the search result to save tokens.
def _summerize(text):
  while gpt.num_tokens_from_messages(text) > _SUMMERIZED_SIZE:
    summaries = []
    num_tokens = gpt.num_tokens_from_messages(text)
    num_buckets = math.ceil(num_tokens / _CHUCK_SIZE)
    bucket_length = math.ceil(len(text) / num_buckets)
    for i in range(num_buckets):
      prompt = f"""
        summerize:
        ```
        {text[i*bucket_length:(i+1)*bucket_length]}
        ```
        into bullet points
        Output format:
        ```
        1.__
        2.__
        ```
        """
      summaries.append(gpt.request(statement=prompt, provider_type=gpt.ProviderType.anthropic, model_type=gpt.ModelType.basic_model))
    text = " \n".join(summaries)
  return text

# Let LLM suggests the keywords for the search.
def _to_keywords(topic:str, search:str)->list[str]:
  prompt = f"""
  If I want to search `{search}` for: `{topic}`, 
  what keywords should I use?

  * Rephrase and expand the question
  * Think step by step (chain of thinking)
  * List the keywords in order of their relevance to effectively search for information.

  Output in the following format:
  ```
  # Rephrased and expanded questions
  *__
  *__
  # Chain of thinking:
  *__
  *__
  # Keywords:
  1. __
  2. __
  """
  # We check multiple(e.g., 4 by default) searchs' results(e.g., by default top 3 result per search) multiple rounds(e.g., by default 3 iterations).
  # By default, we will request gpt 4 * 3 * 3 = 36 times per statement.
  # Use basic model to reduce cost.
  response = gpt.request(statement=prompt, provider_type=gpt.ProviderType.anthropic, model_type=gpt.ModelType.basic_model)
  keywords = []
  keywordSet = set()
  try:
    gpt_suggest = response.split("Keywords")[-1]
  except IndexError:
    return keywords
  raw_keywords = re.findall(r'\d+\.\s+(.*)', gpt_suggest)
  for suggest_keyword in raw_keywords:
    for keyword in suggest_keyword.split(' '):
      if not keyword:
        continue
      parsed_keyword = keyword.lower()
      if parsed_keyword in keywordSet:
        continue
      keywordSet.add(parsed_keyword)
      keywords.append(parsed_keyword)
  return keywords

# Fetch the relevant part of search result.
def _fetch_relevant(text, search):
    relevants = []

    # Function to process each logic and check if it's relevant
    def process_logic(logic):
      if _is_relevant(search, logic):
          return logic
      return None

    # Fetch logics
    logics = logiclinker.fetch_logics(text, gpt.ProviderType.anthropic, gpt.ModelType.basic_model)

    # Use ThreadPoolExecutor to process logics in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map process_logic to each logic
        results = executor.map(process_logic, logics)
        # Filter None values and collect relevant results
        relevants = [result for result in results if result is not None]

    return "\n".join(relevants)

def _fetch_web_content(link, search):
  web_content = webparser.parse(requests.get(link))
  # If we cannot fetch the content from the link.
  if not web_content:
    return ""
  # Find the web content relevant to search.
  relevant_snippet = _fetch_relevant(web_content, search)
  print("relevant snippet:", relevant_snippet)
  return relevant_snippet

# LLM generate keywords to filter search results.
# More key words help us find more precise results, but too many keywords might lead to no results.
# So we need to find the best balance between the number of keywords and the number of results.
def _optimize_search_keywords(search:str, keywords:list[str]):
  num_keywords = len(keywords)
  results = []
  links = set()
  # Search until we have no keywords.
  while num_keywords >=0 :
    keywordStr = ' AND '.join(keywords[:num_keywords])
    url = f"{config['SEARCH']['url']}?key={config['SEARCH']['api_key']}&cx={config['SEARCH']['cx']}&searchTerms={keywordStr}&q={search}&num={_NUM_SEARCH_RESULT}"

    response = requests.get(url)
    data = response.json()
    # If there is no response, we need to reduce the number of keywords.
    if 'items' not in data:
      print(f"query:{search}, keywords:{keywordStr}, got not result: {data}")
      num_keywords -= 1
      continue
    
    # Add new search results, dedup the repeated links.
    for item in data['items']:
      if 'title' in item and 'snippet' in item and 'link' in item:
        if item['link'] not in links:
          links.add(item['link'])
          results.append(item)
    
    # If we got not enough results, continues search with less keywords.
    if len(results) < _NUM_SEARCH_RESULT:
      num_keywords -= 1
      continue
    
    # If we got enough results, we can stop searching.
    return results[:_NUM_SEARCH_RESULT]
  
  # If we cannot find enough results, we need to return the results we got.
  return results

def _web_request(search:str, keywords:list[str]):
  output = []
  items = _optimize_search_keywords(search, keywords)
  for item in items:
    if 'title' in item and 'snippet' in item and 'link' in item:
      summarized_link = item['title'] + item['snippet'] + _fetch_web_content(item['link'], search) + item['link']
      if _is_relevant(search, summarized_link):
        output.append(summarized_link)
  return output

def search(topic:str, max_iter:int)->dict[str,list[str]]:
  results = []
  search_results = {}
  for _ in range(max_iter):
    summerized_result = ''
    if results:
      summerized_result = _summerize(results)

    # Check if the current fact is enough.
    if _is_enough(topic, summerized_result):
      return results

    searches = _to_follow_up_searches(topic, summerized_result)
    for search in searches:
      keywords = _to_keywords(topic, search)
      response = _web_request(search, keywords)
      search_results[search] = response
      results.extend(response)

  return search_results