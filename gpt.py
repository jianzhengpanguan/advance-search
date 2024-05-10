import tiktoken
import requests
import configparser
import anthropic
import math
import ratelimiter
import utils
from applog import logger as logging

_OVERLAP = 40
_MAX_TOKENS = 4000
_TEMPERATURE = 1.0
_GPT_NO_ANSWER = "Sorry, GPT can't answer your question."

# Use tiktoken.get_encoding() to load an encoding by name.
# The first time this runs, it will require an internet connection to download. Later runs won't need an internet connection.
default_encoding = tiktoken.get_encoding("cl100k_base")
# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')
# Limit to 1,000,000 tokens per minute for Anthropic Tier 2 user.
anthropic_token_rate_limiter = ratelimiter.TokensRateLimiter(max_tokens=900000)

def _num_tokens_from_messages(message:str)->int:
  """Return the number of tokens used by messages."""
  if not message:
    return 0
  encoding = default_encoding
  num_tokens = len(encoding.encode(message))
  return num_tokens

def request(statement: str, provider_type: utils.ProviderType=utils.ProviderType.anthropic, model_type: utils.ModelType=utils.ModelType.basic_model)->str:
  if provider_type == utils.ProviderType.anthropic:
    response = anthropic_request(statement, model_type)
    if response != _GPT_NO_ANSWER:
      return response
    # Upgrade to advance model if we still use basic model.
    if model_type == utils.ModelType.basic_model:
      return anthropic_request(statement, utils.ModelType.advance_model)
    # Switch to other provider if advance model still not work.
    return openai_request(statement, utils.ModelType.advance_model)
  
  response = openai_request(statement, model_type)
  if response != _GPT_NO_ANSWER:
    return response
  # Upgrade to advance model if we still use basic model.
  if model_type == utils.ModelType.basic_model:
    return openai_request(statement, utils.ModelType.advance_model)
  # Switch to other provider if advance model still not work.
  return anthropic_request(statement, utils.ModelType.advance_model)

def openai_request(statement:str, model_type:utils.ModelType)->str:
  # Get the OPENAI's API key, url and model from the configuration file.
  headers = {
      'Authorization': f"Bearer {config['OPENAI']['api_key']}",
      'Content-Type': 'application/json'
  }
  # Set model.
  model = config['OPENAI']['advance_model']
  url = config['OPENAI']['advance_url']
  if model_type == utils.ModelType.basic_model:
    model = config['OPENAI']['basic_model']
    url = config['OPENAI']['basic_url']
  statements = divide_statement(statement)
  results = []
  for statement in statements:
    # Find how many tokens used.
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
    if not response or not response.json() or not response.json().get('choices'):
      continue
    logging.info(f"openai response: {response.json().get('choices')}")
    results.append(response.json().get('choices')[0].get('message').get('content'))
  return " \n".join(results)

def anthropic_request(statement:str, model_type:utils.ModelType)->str:
  client = anthropic.Anthropic(
    api_key=config['ANTHROPIC']['api_key'],
  )
  # Set model.
  model = config['ANTHROPIC']['advance_model']
  if model_type == utils.ModelType.basic_model:
    model = config['ANTHROPIC']['basic_model']
  statements = divide_statement(statement)
  results = []
  for statement in statements:
    # Find how many tokens used.
    num_tokens = _num_tokens_from_messages(statement)
    try:
      if anthropic_token_rate_limiter.request_tokens(num_tokens):
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
    response = client.messages.create(
      model=model,
      max_tokens=_MAX_TOKENS - num_tokens,
      temperature=_TEMPERATURE,
      system="",
      messages=messages
    )
    logging.info(f"anthropic response: {response.content}")
    if not len(response.content):
      continue
    results.append(response.content[0].text)
  return " \n".join(results)

# Divide the statement into chunks make sure we don't exceed the maximum number of tokens in one request.
def divide_statement(statement:str)->list[str]:
  """Divide the statement into chunks."""
  num_tokens = _num_tokens_from_messages(statement)
  num_buckets = math.ceil(num_tokens / (_MAX_TOKENS / 2))
  bucket_length = math.ceil(len(statement) / num_buckets)
  return [statement[i:i+bucket_length+_OVERLAP] for i in range(0, len(statement), bucket_length)]