
import requests
import configparser
import anthropic
import utils
from typing import Callable
from applog import logger as logging
from typing import List
import json

_MAX_TOKENS = 4000
_TEMPERATURE = 1.0
_RATE_LIMIT_STATUS_CODE = 429
_SERVER_OVERLOADED_STATUS_CODE= 503
_GPT_NO_ANSWER = "Sorry, GPT can't answer your question."

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
  # Find how many tokens will be used.
  num_tokens = utils.num_tokens_from_messages(statement)
  try:
    logging.info(f"text: {statement} \n, num_tokens_from_messages: {num_tokens}")
  except:
    pass

  # Build the request, including the question or statement you want to ask.
  request = {
      'model': model,
      'temperature': _TEMPERATURE,
      'messages': [{'role': 'user', 'content': statement}],
  }
  response = requests.post(url, headers=headers, json=request)
  logging.info(f"openai response: {response.json()}")
  if response.status_code == _RATE_LIMIT_STATUS_CODE:
    raise RatelimitByProviderError(str(response), response.status_code)
  if not response or not response.json() or not response.json().get('choices'):
    return _GPT_NO_ANSWER
  return response.json().get('choices')[0].get('message').get('content')

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
  # Find how many tokens will be used.
  num_tokens = utils.num_tokens_from_messages(statement)
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
      max_tokens=_MAX_TOKENS, # Required.
      model=model,
      temperature=_TEMPERATURE,
      system="",
      messages=messages
    )
  except anthropic.RateLimitError as e:
    raise RatelimitByProviderError(str(e), response.status_code)
  logging.info(f"anthropic response: {response.content}")
  if not len(response.content):
    return _GPT_NO_ANSWER
  return response.content[0].text

def deepseek_request(statement:str, _:utils.ModelType)->str:
  # Set model.
  model = config['DEEPSEEK']['model']
  url = config['DEEPSEEK']['url']

  # Get the DEEPSEEK's API key, url and model from the configuration file.
  headers = {
      'Authorization': f"Bearer {config['DEEPSEEK']['api_key']}",
      'Content-Type': 'application/json'
  }
  # Find how many tokens will be used.
  num_tokens = utils.num_tokens_from_messages(statement)
  try:
    logging.info(f"text: {statement} \n, num_tokens_from_messages: {num_tokens}")
  except:
    pass

  # Build the request, including the question or statement you want to ask.
  request = {
      'model': model,
      'temperature': _TEMPERATURE,
      "messages": [{"role": "user", "content": statement}],
  }
  response = requests.post(url, headers=headers, json=request)
  if response.status_code == _RATE_LIMIT_STATUS_CODE or response.status_code == _SERVER_OVERLOADED_STATUS_CODE:
    raise RatelimitByProviderError(str(response), response.status_code)
  if not response or not response.json() or not response.json().get('choices'):
    return _GPT_NO_ANSWER
  logging.info(f"Deepseek response: {response.json().get('choices')}")
  return response.json().get('choices')[0].get('message').get('content')


def llama_request(statement:str, model_type:utils.ModelType):
    url = config['LLAMA']['url']
    # Set model.
    model = config['LLAMA']['advance_model']
    if model_type == utils.ModelType.basic_model:
      model = config['LLAMA']['basic_model']
    # Set payload.
    payload = {
        'model': model,
        'prompt': statement,
        'stream': False
    }
    headers = {'Content-Type': 'application/json'}
    try:
      response = requests.post(url, data=json.dumps(payload), headers=headers)
      response.raise_for_status()  # Raises an HTTPError for bad responses
      return response.json()['response']
    except requests.exceptions.HTTPError as http_err:
      logging.warning(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
      logging.warning(f"Request error occurred: {req_err}")
    except json.JSONDecodeError as json_err:
      logging.warning(f"JSON decode error: {json_err}")
    except Exception as e:
      logging.warning("llama_request(): {e}")
    
    return _GPT_NO_ANSWER
