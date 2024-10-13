import utils
import math
import gpt
from typing import List, Callable
import ratelimiter
import retriever
from wrapt_timeout_decorator import timeout
from applog import logger as logging


_OVERLAP = 40
_MAX_TOKENS = 4000
_MAX_RETRIES = 10


# Divide the statement into chunks make sure we don't exceed the maximum number of tokens in one request.
def divide_statement(statement:str, prompt_tokent_count:int)->List[str]:
  """Divide the statement into chunks."""
  if statement == "":
    return [""]
  num_tokens = utils.num_tokens_from_messages(statement)
  if prompt_tokent_count >= _MAX_TOKENS / 2:
    raise ValueError(f"Prompt tokent_count {prompt_tokent_count} exceeds the maximum allowed tokent count of {_MAX_TOKENS} tokens.")
  # For a balanced request/response, the tokens should be evenly distributed between the request and the response.
  # The request tokens = tokens of prompt + tokens of the statement chunk.
  num_buckets = math.ceil(num_tokens / (_MAX_TOKENS / 2 - prompt_tokent_count))
  bucket_tokent_count = math.ceil(len(statement) / num_buckets)
  return [statement[i:i+bucket_tokent_count+_OVERLAP] for i in range(0, len(statement), bucket_tokent_count)]

# When the combined token count of a statement and prompt exceeds _MAX_TOKENS,
# the statement needs to be broken down into segments.
def divide_request(statement: str, model_type:utils.ModelType, query_build_func: Callable[[str], str], request_func: Callable[[str, utils.ModelType], str]) -> List[str]:
  # Check the prompt tokens count without any statement.
  prompt_tokent_count = utils.num_tokens_from_messages(query_build_func(""))

  # If the prompt is excessively long, it results in an excessive number of small segments.
  # For instance, with a prompt of 3999 tokens and a _MAX_TOKENS limit of 4000, each segment of the statement can only be 1 token long.
  # This would mean generating 1000 requests for a 1000-token statement, which is costly and inefficient.
  # In such situations, it's better to directly use the openai retriever assist.
  #
  # For a balanced request/response, the tokens should be evenly distributed between the request and the response.
  # For the request tokens, the tokens should be equally split between the prompt and the statement.
  # So the max prompt tokens should be 1/4 of the max tokens.
  if prompt_tokent_count >= _MAX_TOKENS / 4:
    return [retriever.openai_retrieve(query_build_func("<statemet>\n...\n</statement>"), f"<statemet>\n{statement}\n</statement>", model_type)]

  results = []
  chunks = divide_statement(statement, prompt_tokent_count)
  for current_chunk in chunks:
    query = query_build_func(current_chunk)
    results.append(request_func(query, model_type))
  return results

class model:
  provider_type: utils.ProviderType
  model_type: utils.ModelType
  per_minute_rate_limiter: ratelimiter.PerMinuteRateLimiter
  isRateLimitedByProvider: bool
  request_function: Callable[[str, utils.ModelType], str]

  def __init__(self, provider_type=utils.ProviderType, model_type=utils.ModelType.basic_model, per_minute_rate_limiter=None, request_function=gpt.anthropic_request) -> None:
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
  models: List[model]

  def __init__(self, models) -> None:
    self.models = models
  
  def _is_all_models_rate_limit_by_provider(self) -> bool:
    for model in self.models:
      if not model.isRateLimitedByProvider:
        return False
    return True

  def request(self, statement: str, query_build_func: Callable[[str], str])->List[str]:
    # Find how many tokens will be used.
    prompt = query_build_func("")
    num_tokens = utils.num_tokens_from_messages(f"{statement} {prompt}")
    for _ in range(_MAX_RETRIES):
      if self._is_all_models_rate_limit_by_provider():
        raise gpt.RatelimitByProviderError("All providers and models are rate limited.", gpt._RATE_LIMIT_STATUS_CODE)
      for model in self.models:
        if not model.per_minute_rate_limiter.allow_request_tokens(num_tokens):
          continue
        if model.isRateLimitedByProvider:
          continue
        try:
          response = divide_request(statement, model.model_type, query_build_func, model.request)
        except gpt.RatelimitByProviderError:
          logging.warning(f"Provider:{model.provider_type} Model:{model.model_type} is rate limited by provider, moved to the next provider and model")
          model.isRateLimitedByProvider = True
          continue
        # If the current model cannot answer the question, move to the next model.
        if response == gpt._GPT_NO_ANSWER:
          logging.warning(f"Provider:{model.provider_type} Model:{model.model_type} cannot answer the question, moved to the next provider and model")
          continue
        if response == None:
          logging.warning(f"Provider:{model.provider_type} Model:{model.model_type} does not answer the question, moved to the next provider and model")
          continue
        return response

# Cheapest model first.
basic_models = [
  model(
    provider_type=utils.ProviderType.llama,
    model_type=utils.ModelType.basic_model,
    request_function=gpt.llama_request,
    per_minute_rate_limiter=ratelimiter.PerMinuteRateLimiter(name=f"Provider:{utils.ProviderType.llama},Model:{utils.ModelType.basic_model}", max_num_requests=5),
  ),
  model(
    provider_type=utils.ProviderType.openai,
    model_type=utils.ModelType.basic_model,
    request_function=gpt.openai_request,
    per_minute_rate_limiter=ratelimiter.PerMinuteRateLimiter(name=f"Provider:{utils.ProviderType.openai},Model:{utils.ModelType.basic_model}", max_num_requests=120),
  ),
  model(
    provider_type=utils.ProviderType.deepseek,
    model_type=utils.ModelType.basic_model,
    request_function=gpt.deepseek_request,
  ),
  model(
    provider_type=utils.ProviderType.anthropic,
    model_type=utils.ModelType.basic_model,
    request_function=gpt.anthropic_request,
  ),
]
basic_models_requester = requester(basic_models)

# Timeout the gpt request if it takes more than 300 seconds.
@timeout(300)
def request(statement:str, query_build_func: Callable[[str], str])->List[str]:
  return basic_models_requester.request(statement, query_build_func)
