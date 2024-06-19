import tiktoken
import requests
import configparser
import anthropic
import math
import ratelimiter
import utils
from wrapt_timeout_decorator import timeout
from typing import Callable
from applog import logger as logging

_OVERLAP = 40
_MAX_TOKENS = 4000
_TEMPERATURE = 1.0
_MAX_RETRIES = 10
_RATE_LIMIT_STATUS_CODE = 429
_SERVER_OVERLOADED_STATUS_CODE= 503
_GPT_NO_ANSWER = "Sorry, GPT can't answer your question."

# Use tiktoken.get_encoding() to load an encoding by name.
# The first time this runs, it will require an internet connection to download. Later runs won't need an internet connection.
default_encoding = tiktoken.get_encoding("cl100k_base")
# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')


class RatelimitByProviderError(Exception):
  response: str
  status_code: int

  def __init__(self, response, status_code) -> None:
    self.response = response
    self.status_code = status_code


def _num_tokens_from_messages(message:str)->int:
  """Return the number of tokens used by messages."""
  if not message:
    return 0
  encoding = default_encoding
  num_tokens = len(encoding.encode(message))
  return num_tokens

def openai_request(statement:str, model_type:utils.ModelType)->str:
  # Set model.
  url = config['OPENAI']['url']
  model = config['OPENAI']['advance_model']
  if model_type == utils.ModelType.basic_model:
    model = config['OPENAI']['basic_model']
  # Get the OPENAI's API key, url and model from the configuration file.
  headers = {
      'Authorization': f"Bearer {config['OPENAI']['api_key']}",
      'Content-Type': 'application/json'
  }
  statements = divide_statement(statement)
  results = []
  for statement in statements:
    # Find how many tokens will be used.
    num_tokens = _num_tokens_from_messages(statement)
    try:
      logging.info(f"text: {statement} \n, num_tokens_from_messages: {num_tokens}")
    except:
      pass

    # Build the request, including the question or statement you want to ask.
    request = {
        'model': model,
        'temperature': _TEMPERATURE,
        'messages': [{'role': 'user', 'content': statement}],
        'max_tokens': _MAX_TOKENS - num_tokens
    }
    response = requests.post(url, headers=headers, json=request)
    logging.info(f"openai response: {response.json()}")
    if response.status_code == _RATE_LIMIT_STATUS_CODE:
      raise RatelimitByProviderError(str(response), response.status_code)
    if not response or not response.json() or not response.json().get('choices'):
      continue
    results.append(response.json().get('choices')[0].get('message').get('content'))
  return " \n".join(results)

def anthropic_request(statement:str, model_type:utils.ModelType)->str:
  # Set model.
  model = config['ANTHROPIC']['advance_model']
  if model_type == utils.ModelType.basic_model:
    model = config['ANTHROPIC']['basic_model']
  if model_type == utils.ModelType.small_model:
    model = config['ANTHROPIC']['small_model']
  # Init client.
  client = anthropic.Anthropic(
    api_key=config['ANTHROPIC']['api_key'],
  )
  statements = divide_statement(statement)
  results = []
  for statement in statements:
    # Find how many tokens will be used.
    num_tokens = _num_tokens_from_messages(statement)
    try:
      logging.info(f"text: {statement} \n, num_tokens_from_messages: {num_tokens}")
    except:
      pass

    # Build the message, including the question or statement you want to ask.
    messages = [{
      "role": "user", 
      "content": [
        {
          "type": "text",
          "text": statement
        }
      ]
    }]
    try:
      response = client.messages.create(
        model=model,
        max_tokens=_MAX_TOKENS - num_tokens,
        temperature=_TEMPERATURE,
        system="",
        messages=messages
      )
    except anthropic.RateLimitError as e:
      raise RatelimitByProviderError(str(e), response.status_code)
    logging.info(f"anthropic response: {response.content}")
    if not len(response.content):
      continue
    results.append(response.content[0].text)
  return " \n".join(results)

def deepseek_request(statement:str, _:utils.ModelType)->str:
  # Set model.
  model = config['DEEPSEEK']['model']
  url = config['DEEPSEEK']['url']

  # Get the DEEPSEEK's API key, url and model from the configuration file.
  headers = {
      'Authorization': f"Bearer {config['DEEPSEEK']['api_key']}",
      'Content-Type': 'application/json'
  }
  statements = divide_statement(statement)
  results = []
  for statement in statements:
    # Find how many tokens will be used.
    num_tokens = _num_tokens_from_messages(statement)
    try:
      logging.info(f"text: {statement} \n, num_tokens_from_messages: {num_tokens}")
    except:
      pass

    # Build the request, including the question or statement you want to ask.
    request = {
        'model': model,
        'temperature': _TEMPERATURE,
        "messages": [{"role": "user", "content": statement}],
        'max_tokens': _MAX_TOKENS - num_tokens
    }
    response = requests.post(url, headers=headers, json=request)
    if response.status_code == _RATE_LIMIT_STATUS_CODE or response.status_code == _SERVER_OVERLOADED_STATUS_CODE:
      raise RatelimitByProviderError(str(response), response.status_code)
    if not response or not response.json() or not response.json().get('choices'):
      continue
    logging.info(f"Deepseek response: {response.json().get('choices')}")
    results.append(response.json().get('choices')[0].get('message').get('content'))
  return " \n".join(results)

# Divide the statement into chunks make sure we don't exceed the maximum number of tokens in one request.
def divide_statement(statement:str)->list[str]:
  """Divide the statement into chunks."""
  num_tokens = _num_tokens_from_messages(statement)
  num_buckets = math.ceil(num_tokens / (_MAX_TOKENS / 4))
  bucket_length = math.ceil(len(statement) / num_buckets)
  return [statement[i:i+bucket_length+_OVERLAP] for i in range(0, len(statement), bucket_length)]

class model:
  provider_type: utils.ProviderType
  model_type: utils.ModelType
  per_minute_rate_limiter: ratelimiter.PerMinuteRateLimiter
  isRateLimitedByProvider: bool
  request_function: Callable[[str, utils.ModelType], str]

  def __init__(self, provider_type=utils.ProviderType, model_type=utils.ModelType.basic_model, per_minute_rate_limiter=None, request_function=anthropic_request) -> None:
    if per_minute_rate_limiter is None:
      per_minute_rate_limiter = ratelimiter.PerMinuteRateLimiter(name=f"Provider:{provider_type},Model:{model_type}")
    self.provider_type = provider_type
    self.model_type = model_type
    self.per_minute_rate_limiter = per_minute_rate_limiter
    self.isRateLimitedByProvider = False
    self.request_function = request_function
  
  def request(self, statement:str, model_type:utils.ModelType)->str:
    """Request a response from the model."""
    if not statement:
      return ""
    if self.isRateLimitedByProvider:
      return ""
    if model_type != self.model_type:
      return self.request_function(statement, model_type)
    return self.request_function(statement, self.model_type)
  
class requester:
  models: list[model]

  def __init__(self, models) -> None:
    self.models = models
  
  def _is_all_models_rate_limit_by_provider(self) -> bool:
    for model in self.models:
      if not model.isRateLimitedByProvider:
        return False
    return True

  def request(self, statement: str)->str:
    # Find how many tokens will be used.
    num_tokens = _num_tokens_from_messages(statement)
    for _ in range(_MAX_RETRIES):
      if self._is_all_models_rate_limit_by_provider():
        raise RatelimitByProviderError("All providers and models are rate limited.", _RATE_LIMIT_STATUS_CODE)
      for model in self.models:
        if not model.per_minute_rate_limiter.allow_request_tokens(num_tokens):
          continue
        if model.isRateLimitedByProvider:
          continue
        try:
          response = model.request(statement, model.model_type)
        except RatelimitByProviderError as e:
          logging.warning(f"Provider:{model.provider_type} Model:{model.model_type} is rate limited by provider, moved to the next provider and model")
          model.isRateLimitedByProvider = True
          continue
        # If the current model cannot answer the question, move to the next model.
        if response == _GPT_NO_ANSWER:
          logging.warning(f"Provider:{model.provider_type} Model:{model.model_type} cannot answer the question, moved to the next provider and model")
          continue
        if response == None:
          logging.warning(f"Provider:{model.provider_type} Model:{model.model_type} cannot answer the question, moved to the next provider and model")
          continue
        return response

# Cheapest model first.
basic_models = [
  model(
    provider_type=utils.ProviderType.openai,
    model_type=utils.ModelType.basic_model,
    request_function=openai_request,
    per_minute_rate_limiter=ratelimiter.PerMinuteRateLimiter(name=f"Provider:{utils.ProviderType.openai},Model:{utils.ModelType.basic_model}", max_num_requests=12),
  ),
  model(
    provider_type=utils.ProviderType.deepseek,
    model_type=utils.ModelType.basic_model,
    request_function=deepseek_request,
  ),
  model(
    provider_type=utils.ProviderType.anthropic,
    model_type=utils.ModelType.basic_model,
    request_function=anthropic_request,
  ),
]
basic_models_requester = requester(basic_models)

# Timeout the gpt request if it takes more than 300 seconds.
@timeout(300)
def request(statement:str)->str:
  return basic_models_requester.request(statement)
