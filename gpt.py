import tiktoken
import requests
import configparser

_MAX_TOKENS = 4000
_TEMPERATURE = 1.0

# Use tiktoken.get_encoding() to load an encoding by name.
# The first time this runs, it will require an internet connection to download. Later runs won't need an internet connection.
encoding = tiktoken.get_encoding("cl100k_base")
# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config.ini')


def _num_tokens_from_messages(message, model):
    """Return the number of tokens used by messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using default cl100k_base encoding.")
    num_tokens = len(encoding.encode(message))
    return num_tokens

def request(statement):
  model = config['LLM']['model']
  # Get the LLM's API key, url and model from the configuration file.
  headers = {
      'Authorization': f"Bearer {config['LLM']['api_key']}",
      'Content-Type': 'application/json'
  }
  num_tokens = _num_tokens_from_messages(statement, model)
  try:
    print(f"text: {statement} \n, num_tokens_from_messages: {num_tokens}")
  except:
    pass

  # Build the request, including the question or statement you want to ask.
  request = {
      'model': model,
      'temperature': _TEMPERATURE,
      "messages": [{"role": "user", "content": statement}],
      'max_tokens': _MAX_TOKENS - num_tokens
  }

  response = requests.post(config['LLM']['url'], headers=headers, json=request)
  if not response.json().get('choices'):
      return "Sorry, I can't answer your question."
  return response.json().get('choices')[0].get('message').get('content')
