import requests
import re
import gpt
import configparser
import webparser
import logiclinker
import retriever
import rephraser
import concurrent.futures
import utils
import json
from applog import logger as logging
from typing import List, Dict

_MAX_WORKERS = 12 # The maximum number of requests allowed by most LLM api.
_NUM_TARGET_SEARCH_RESULT = 5
_NUM_SEARCHES = 5
_MAX_LINKS_PER_SEARCH = 20
_MAX_LINKS_PER_QUERY = 10
_MAX_ALLOWED_SEARCH_RESULT_SIZE = 100000


# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')

# Given the search result, determine if the search result is relevant to the statement.
def _is_relevant(statement:str, search_result:str)->bool:
  prompt = f"""
    Given search result ```
    %s
    ```
    is that relevant to statement `%s`? 
    
    * Think step by step (chain of thinking)
    * Answer the yes/no.

    Output in the following format:
    ```
    # Chain of thinking:
    *__
    *__
    # Answer:
    yes/no
    ```
  """
  # Need to divide the search result into chunks.
  def query_build_func(chunk: str) -> str:
    return prompt % (chunk, statement)
  
  # We check multiple(e.g., 4 by default) searchs' results(e.g., by default top 3 result per search) multiple rounds(e.g., by default 3 iterations).
  # By default, we will request gpt 4 * 3 * 3 = 36 times per statement.
  # Use basic model to reduce cost.
  try:
    response = "\n".join(gpt.request(search_result, query_build_func))
  except Exception as e:
    logging.error(f"Error when requesting GPT, gpt.request({search_result} {query_build_func('')}): {e}")
    return False

  answer = ""
  try:
    answer = response.split("Answer")[-1]
  except IndexError:
    logging.error(f"Cannot find 'Answer' in response: {response}")
  except AttributeError:
    logging.error(f"Response is None type: {response}")
  if 'yes' in answer.lower():
    return True
  return False

def _summarize(statement:str, search_result:str)->List[str]:
  if not statement or not search_result:
    return []
  prompt = f"""
  Given the document.

  Please summarize the parts of this document that are relevant to the following statement:  
  <statement>`{statement}`</statement>

  First, carefully read the document and statement. 
  Then, in a <scratchpad>, think through step-by-step how to summarize the document in a way that extracts only the parts that are relevant to the given statement. 

  Then, provide a numbered list summarizing the key points from the document that relate to the statement. Format your summary like this:

  ```
  # Chain of thinking:
  *__
  *__
  # Summary:
  1.__
  2.__
  3.__
  ```

  Each point should be one sentence long at most. Focus on distilling out only the essential information that pertains to the given statement.
  """
  response = retriever.retrieve(prompt, search_result, utils.ProviderType.openai)
  answer = ""
  try:
    answer = response.split("Summary")[-1]
  except IndexError:
    logging.error(f"Cannot find 'Summary' in response: {response}")
  except AttributeError:
    logging.error(f"Response is None type: {response}")
  return re.findall(r'\d+\.\s+(.*)', answer)


# Given the search result, determine if additional search is needed.
def _is_enough(statement:str, search_result:str, search_type:utils.SearchType=utils.SearchType.verifier):
  if not search_result:
    return False
  
  if len(search_result) > _MAX_ALLOWED_SEARCH_RESULT_SIZE:
    return True

  prompt = f"""
  Given the document: 
  ```
  %s
  ```
  is there enough information for you to %s: `%s`? 
  
  * Think step by step (chain of thinking)
  * Answer the yes/no.

  Output in the following format:
  ```
  # Chain of thinking:
  *__
  *__
  # Answer:
  yes/no
  ```
  """
  # Need to divide the search result into chunks.
  def query_build_func(chunk: str) -> str:
    return prompt % (chunk, search_type.value, statement)
  
  response = "\n".join(gpt.divide_request(statement, utils.ModelType.advance_model, query_build_func, gpt.openai_request))

  answer = ""
  try:
    answer = response.split("Answer")[-1]
  except IndexError:
    logging.error(f"Cannot find 'Answer' in response: {response}")
  except AttributeError:
    logging.error(f"Response is None type: {response}")
  if 'yes' in answer.lower():
    return True
  return False

# Based on the searched result, let LLM define follow up search questions.
def _to_follow_up_searches(statement:str, search_result:str, search_type:utils.SearchType=utils.SearchType.verifier)->Dict[str,str]:
  prompt = f"""
  You will be helping to {search_type.value} a `{statement}` by suggesting relevant searches. 
  
  First, think step-by-step about what searches would be most relevant and helpful for {search_type.value} the given statement. 
  Write out your step-by-step reasoning.

  Then, list out the searches you came up with in order of relevance for {search_type.value} the statement.

  Finally, explain why each of the searches you listed helps {search_type.value} the original statement.

  ```
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
  if search_result:
    retriever_prefix = f"The given document is not enough to {search_type.value}: `{statement}`"
    response = retriever.retrieve(f"{retriever_prefix}\n{prompt}", search_result, utils.ProviderType.openai)
  else:
    response = gpt.openai_request(prompt, utils.ModelType.advance_model)
  logging.info(f"_to_follow_up_searches():{response}")
  try:
    response_without_explain, explain_search = response.split("Explain")[:-1], response.split("Explain")[-1]
  except IndexError:
    logging.error(f"Cannot find 'Explain' in response: {response}")
  except AttributeError:
    logging.error(f"Response is None type: {response}")
  explains = re.findall(r'\d+\.\s+(.*)', explain_search)
  try:
    suggest_search = "".join(response_without_explain).split("Search")[-1]
  except IndexError:
    logging.error(f"Cannot find 'Search' in response: {response}")
  except AttributeError:
    logging.error(f"Response is None type: {response}")
  searches = re.findall(r'\d+\.\s+(.*)', suggest_search)
  search_explains = {}
  num_searches = min(len(searches), len(explains), _NUM_SEARCHES)
  for i in range(num_searches):
    rephrased_search = rephraser.stonealone_question(searches[i])
    if _is_relevant(statement, rephrased_search):
      search_explains[rephrased_search] = explains[i]
    else:
      logging.warning(f"search: {rephrased_search} is not relevant to {statement}")
  return search_explains

# Let LLM suggests the keywords for the search.
def _to_keywords(topic:str, search:str, search_type:utils.SearchType=utils.SearchType.verifier)->List[str]:
  prompt = f"""
  If I want to search ```
  {search}
  ```
  to {search_type.value}: 
  ```
  {topic}
  ```
  what keywords should I use?

  * Think step by step (chain of thinking)
  * List the keywords in order of their relevance to effectively search for information.

  Output in the following format:
  ```
  # Chain of thinking:
  *__
  *__
  # Keywords:
  1. __
  2. __
  """
  keywords = []
  keywordSet = set()
  # We check multiple(e.g., 4 by default) searchs' results(e.g., by default top 3 result per search) multiple rounds(e.g., by default 3 iterations).
  # By default, we will request gpt 4 * 3 * 3 = 36 times per statement.
  # Use basic model to reduce cost.
  try:
    response = gpt.openai_request(prompt, utils.ModelType.advance_model)
  except Exception as e:
    logging.error(f"Error when requesting GPT, gpt.request({prompt}): {e}")
    return keywords

  gpt_suggest = ""
  try:
    gpt_suggest = response.split("Keywords")[-1]
  except IndexError:
    logging.error(f"Cannot find 'Keywords' in response: {response}")
  except AttributeError:
    logging.error(f"Response is None type: {response}")
  if not gpt_suggest:
    return keywords

  raw_keywords = re.findall(r'\d+\.\s+(.*)', gpt_suggest)
  for suggest_keyword in raw_keywords:
    if not suggest_keyword:
      continue
    for keyword in suggest_keyword.split(' '):
      if not keyword:
        continue
      parsed_keyword = keyword.lower()
      if parsed_keyword in keywordSet:
        continue
      keywordSet.add(parsed_keyword)
      keywords.append(parsed_keyword)
  return keywords

def _fetch_web_content(link:str, search:str)->str:
  try:
    web_content = webparser.parse(link)
  except Exception as e:
    logging.info(f"Cannot fetch web content webparser.parse({link}): {e}")
    return ""
  # If we cannot fetch the content from the link.
  if not web_content:
    return ""
  # Find the web content relevant to search.
  relevant_snippet = retriever.retrieve(search, web_content)
  return relevant_snippet

# LLM generate keywords to filter search results.
def _optimize_search(search:str, keywords:List[str]):
  results = []
  links = set()
  for start in range(1, _MAX_LINKS_PER_SEARCH, _MAX_LINKS_PER_QUERY):
    url = f"{config['SEARCH']['url']}?key={config['SEARCH']['api_key']}&cx={config['SEARCH']['cx']}&safe=active&q={search}&orTerms={' '.join(keywords)}&num={_MAX_LINKS_PER_QUERY}&start={start}"

    try:
      response = requests.get(url, timeout=60)  # Timeout set to 60 seconds
    except requests.exceptions.Timeout:
      logging.error("The request timed out: %s", url)
      continue
    data = response.json()
    # If there is no response, we need to reduce the number of keywords.
    if 'items' not in data:
      logging.info(f"query:{search}, keywords:{keywords}, got not result: {data}")
      break
    
    # Add new search results, dedup the repeated links.
    for item in data['items']:
      if not ('title' in item and 'snippet' in item and 'link' in item):
        continue
      # Check if the link title and snippest is revelant to the search.
      if not _is_relevant(search, f"{item['title']} {item['snippet']}"):
        continue
      if item['link'] not in links:
        links.add(item['link'])
        results.append(item)
        if len(results) >= _NUM_TARGET_SEARCH_RESULT:
          break
      
      # If we got enough results, we can stop searching.
      if len(results) >= _NUM_TARGET_SEARCH_RESULT:
        break
  return results

def _web_request(search:str, keywords:List[str])->List[Dict[str, str]]:
  items = _optimize_search(search, keywords)

  # Function to process each item and check if it's relevant
  def process(item)->Dict[str, str]:
    if 'title' in item and 'snippet' in item and 'link' in item:
      # Fetch web content will get the chuck based on the question (e.g, search/title/snippet).
      # Dedup the same chuck retrived from different questions.
      knowledges = set()
      for question in [search, item['title'], item['snippet']]:
        knowledge_from_web = _fetch_web_content(item['link'], question)
        knowledges.add(knowledge_from_web)
      knowledge = "\n".join(knowledges)
      # Summerized the knowledge.
      relevant_knowledge = _summarize(search, knowledge)
      if not _is_relevant(search, "\n".join(relevant_knowledge)):
        return None
      # Only keep the logic relevant to the search.
      logics =  logiclinker.fetch_logics(knowledge)
      relevant_logics = []
      for logic in logics:
        if _is_relevant(search, str(logic)):
          relevant_logics.append(logic)

    return {
      "title": item['title'],
      "snippet": item['snippet'],
      "logics": relevant_logics,
      "knowledge": relevant_knowledge,
      "link": item['link']
    }

  # Use ThreadPoolExecutor to process items in parallel
  with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKERS) as executor:
    # Map process to each item.
    results = executor.map(process, items)
    # Filter None values and collect relevant results
    return [result for result in results if result is not None]

class SearchResults:
  def __init__(self, search:str, explain:str, results:List[Dict[str, str]]):
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


def search(topic:str, max_iter:int, search_type:utils.SearchType=utils.SearchType.verifier)->List[SearchResults]:
  search_results:List[SearchResults] = []
  results = []
  
  # If we want to verify a premise or hypothesis, we can directly search it to see if there are any answer.
  if search_type == utils.SearchType.verifier:
    response = ""
    try:
      response = _web_request(topic, _to_keywords(topic, topic, search_type))
    except Exception as e:
      logging.error(f"_web_request({topic}, {search_type}): {e}")
    search_results.append(SearchResults(search=topic, explain="Original topic", results=response))
    results.extend(response)
  for _ in range(max_iter):
    all_results = "\n".join([str(result) for result in results])
    summerized_results = "\n".join(_summarize(topic, all_results))
    # Check if the current fact is enough.
    if _is_enough(topic, summerized_results):
      return search_results
    search_explains = None
    try:
      search_explains = _to_follow_up_searches(topic, summerized_results, search_type)
    except Exception as e:
      logging.error(f" _to_follow_up_searches({topic}, {summerized_results}, {search_type}): {e}")
    if not search_results:
      continue
    for search, explain in search_explains.items():
      response = ""
      try:
        response = _web_request(search, _to_keywords(topic, search, search_type))
      except Exception as e:
        logging.error(f"_web_request({topic}, {search}, {search_type}): {e}")
      search_results.append(SearchResults(search=search, explain=explain, results=response))
      results.extend(response)
  
  # Try to return as much search results as possible.
  return search_results
