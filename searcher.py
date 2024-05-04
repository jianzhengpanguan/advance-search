import requests
import re
import gpt
import configparser
import webparser
import math
import logiclinker
import retriever
import concurrent.futures
import utils
import json

_MAX_WORKERS = 1
_NUM_SEARCH_RESULT = 5
_NUM_SEARCHES = 5
_CHUCK_SIZE = 500
_SUMMERIZED_SIZE = 100

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')

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
  response = gpt.request(statement=prompt, provider_type=utils.ProviderType.anthropic, model_type=utils.ModelType.basic_model)
  try:
    answer = response.split("Answer")[-1]
  except IndexError:
    return False
  if 'Yes' in answer:
    return True
  return False

# Given the search result, determine if additional search is needed.
def _is_enough(statement:str, search_result:str, search_type:utils.SearchType=utils.SearchType.verifier):
  if not search_result:
    return False

  prompt = f"""
  Given `{search_result}`
  can you {search_type.value}: `{statement}`? 
  
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
def _to_follow_up_searches(statement:str, search_result:str, search_type:utils.SearchType=utils.SearchType.verifier)->dict[str,str]:
  prompt = f"""
  Given `{search_result}`
  If I want to {search_type.value}: `{statement}`
  what else should I search?

  * Rephrase and expand the question
  * Think step by step (chain of thinking)
  * List the searches in order of their relevance to effectively {search_type.value}
  * Explain why the search helps to {search_type.value}

  Output in the following format:
  ```
  # Rephrased and expanded questions
  *__
  *__
  # Chain of thinking:
  *__
  *__
  # Search:
  1.__
  2.__
  # Explain:
  1.__
  2.__
  ```
  """
  response = gpt.request(prompt)
  print("_to_follow_up_searches():", response)
  response_without_explain, explain_search = response.split("Explain")[:-1], response.split("Explain")[-1]
  explains = re.findall(r'\d+\.\s+(.*)', explain_search)
  suggest_search = "".join(response_without_explain).split("Search")[-1]
  searches = re.findall(r'\d+\.\s+(.*)', suggest_search)
  search_explains = {}
  num_searches = min(len(searches), len(explains), _NUM_SEARCHES)
  for i in range(num_searches):
    search_explains[searches[i]] = explains[i]
  return search_explains

# Summerize the search result to save tokens.
def _summerize(text, max_iter):
  for i in range(max_iter):
    if gpt.num_tokens_from_messages(text) < _SUMMERIZED_SIZE:
      break
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
      summaries.append(gpt.request(statement=prompt, provider_type=utils.ProviderType.anthropic, model_type=utils.ModelType.basic_model))
    text = " \n".join(summaries)
  return text

# Let LLM suggests the keywords for the search.
def _to_keywords(topic:str, search:str, search_type:utils.SearchType=utils.SearchType.verifier)->list[str]:
  prompt = f"""
  If I want to search ```
  {search}
  ```
  to {search_type.value}: 
  ```
  {topic}
  ```
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
  response = gpt.request(statement=prompt, provider_type=utils.ProviderType.anthropic, model_type=utils.ModelType.basic_model)
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

def _fetch_web_content(link, search):
  web_content = webparser.parse(link)
  # If we cannot fetch the content from the link.
  if not web_content:
    return ""
  # Find the web content relevant to search.
  relevant_snippet = retriever.retrieve(search, web_content)
  print("relevant snippet:", relevant_snippet)
  return relevant_snippet

# LLM generate keywords to filter search results.
# More key words help us find more precise results, but too many keywords might lead to no results.
# So we need to find the best balance between the number of keywords and the number of results.
def _optimize_search(search:str, keywords:list[str]):
  num_keywords = len(keywords)
  results = []
  links = set()
  # Search until we have no keywords.
  while num_keywords >=0 :
    keywordStr = ' AND '.join(keywords[:num_keywords])
    url = f"{config['SEARCH']['url']}?key={config['SEARCH']['api_key']}&cx={config['SEARCH']['cx']}&searchTerms={keywordStr}&q={search}&num={_NUM_SEARCH_RESULT}"

    response = requests.get(url, timeout=60)  # Timeout set to 60 seconds
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
  items = _optimize_search(search, keywords)

  # Function to process each item and check if it's relevant
  def process(item):
    if 'title' in item and 'snippet' in item and 'link' in item:
      knowledge_from_web = _fetch_web_content(item['link'], search)
      if not _is_relevant(search, knowledge_from_web):
        return None
      # Fetch logics
      logics = logiclinker.fetch_logics(knowledge_from_web, utils.ProviderType.anthropic, utils.ModelType.basic_model)
    return item['title'] + item['snippet'] + str(logics) + item['link']

  # Use ThreadPoolExecutor to process items in parallel
  with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
    # Map process to each item.
    results = executor.map(process, items)
    # Filter None values and collect relevant results
    return [result for result in results if result is not None]

class SearchResults:
  def __init__(self, search:str, explain:str, results:list[str]):
    self.search = search
    self.explain = explain
    self.results = results

  def __str__(self):
    return f"Search: {self.search}, Explain: {self.explain}, Results: {self.results}"

  def to_dict(self):
    return {
      "search": self.search,
      "explain": self.explain,
      "results": self.results
    }

class CustomEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, SearchResults):
        return obj.to_dict()
    # If the object is of any other type, use the default behavior
    return json.JSONEncoder.default(self, obj)


def search(topic:str, max_iter:int, search_type:utils.SearchType=utils.SearchType.verifier)->list[SearchResults]:
  search_results:list[SearchResults] = []
  results = []
  # If we want to verify a premise or hypothesis, we can directly search it to see if there are any answer.
  if search_type == utils.SearchType.verifier:
    response = _web_request(topic, _to_keywords(topic, topic, search_type))
    search_results.append(SearchResults(search=topic, explain="Original topic", results=response))
    results.extend(response)
  for _ in range(max_iter):
    summerized_result = _summerize("\n".join(results), max_iter)
    # Check if the current fact is enough.
    if _is_enough(topic, summerized_result):
      return search_results

    search_explains = _to_follow_up_searches(topic, summerized_result, search_type)
    for search, explain in search_explains.items():
      keywords = _to_keywords(topic, search, search_type)
      response = _web_request(search, keywords)
      search_results.append(SearchResults(search=search, explain=explain, results=response))
      results.extend(response)

  return search_results