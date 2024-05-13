from enum import Enum
import json


class ProviderType(Enum):
  unknown = 0
  openai = 1
  anthropic = 2
  deepseek = 3

class ModelType(Enum):
  advance_model = 1
  basic_model = 2

class SearchType(Enum):
  verifier = "verify"
  fallacy_avoider = "avoid the fallacy"
