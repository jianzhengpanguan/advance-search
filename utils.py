from enum import Enum
import json


class ProviderType(Enum):
  unknown = 0
  openai = 1
  anthropic = 2
  deepseek = 3

class ModelType(Enum):
  basic_model = 0
  advance_model = 1
  small_model = 2

class SearchType(Enum):
  verifier = "verify"
