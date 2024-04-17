from enum import Enum

class ProviderType(Enum):
  unknown = 0
  openai = 1
  anthropic = 2

class ModelType(Enum):
  advance_model = 1
  basic_model = 2