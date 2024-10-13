import tiktoken
from enum import Enum
import json


class ProviderType(Enum):
  unknown = 0
  openai = 1
  anthropic = 2
  deepseek = 3
  llama = 4

class ModelType(Enum):
  basic_model = 0
  advance_model = 1
  small_model = 2

class SearchType(Enum):
  verifier = "verify"
  image_search = "to search images"


# Use tiktoken.get_encoding() to load an encoding by name.
# The first time this runs, it will require an internet connection to download. Later runs won't need an internet connection.
default_encoding = tiktoken.get_encoding("cl100k_base")


def num_tokens_from_messages(message:str)->int:
  """Return the number of tokens used by messages."""
  if not message:
    return 0
  encoding = default_encoding
  num_tokens = len(encoding.encode(message))
  return num_tokens