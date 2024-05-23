import time
from applog import logger as logging
import threading

class PerMinuteRateLimiter:
  def __init__(self, name, max_tokens=90000, max_num_requests=6):
    self.name = name # Rate limiter model name.
    self.max_tokens = max_tokens  # Maximum tokens allowed per minute
    self.max_num_requests = max_num_requests # Maximum number of request allowed per minute
    self.token_usage = []  # List to store tuples of (timestamp, tokens_used)
    self.lock = threading.Lock()  # Lock to synchronize access

  def _remove_old_tokens(self):
    """Remove token records that are older than one minute."""
    one_minute_ago = time.time() - 60
    while self.token_usage and self.token_usage[0][0] < one_minute_ago:
      self.token_usage.pop(0)

  def allow_request_tokens(self, tokens_needed:int)->bool:
    """Attempt to request a certain number of tokens. Return True if allowed, False if rate limit exceeded."""
    with self.lock:
      self._remove_old_tokens()
      # Check number of requests limit.
      if len(self.token_usage) > self.max_num_requests:
        logging.info(f"{self.name} rate limit exceeded. Number of requests:{len(self.token_usage)} exceeds the limit:{self.max_num_requests}.")
        return False
      current_tokens_used = sum(tokens for _, tokens in self.token_usage)
      # Check rate limit
      if current_tokens_used + tokens_needed > self.max_tokens:
        logging.info(f"{self.name} rate limit exceeded. Current tokens used:{current_tokens_used}, tokens needed:{tokens_needed}, max tokens:{self.max_tokens}.")
        return False
      self.token_usage.append((time.time(), tokens_needed))
      return True
