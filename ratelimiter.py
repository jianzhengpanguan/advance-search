import time
import logging

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)


class TokensRateLimiter:
  def __init__(self, max_tokens):
    self.max_tokens = max_tokens  # Maximum tokens allowed per minute
    self.token_usage = []  # List to store tuples of (timestamp, tokens_used)

  def _remove_old_tokens(self):
    """Remove token records that are older than one minute."""
    one_minute_ago = time.time() - 60
    while self.token_usage and self.token_usage[0][0] < one_minute_ago:
      self.token_usage.pop(0)

  def request_tokens(self, tokens_needed):
    """Request a certain number of tokens. If rate limit is exceeded, wait and try again."""
    while True:
      self._remove_old_tokens()
      # Max 1 request per second.
      one_second_ago = time.time() - 1
      if self.token_usage and self.token_usage[-1][0] >= one_second_ago:
        logging.info(f"Tokens requested: {tokens_needed} too frequently at {time.ctime()}, wait for one second.\n")
        time.sleep(1)
        continue

      current_tokens_used = sum(tokens for _, tokens in self.token_usage)
      logging.info(f"Tokens used: {current_tokens_used}, new tokens requested: {tokens_needed} in last minute at {time.ctime()}\n")
      
      if current_tokens_used + tokens_needed <= self.max_tokens:
          self.token_usage.append((time.time(), tokens_needed))
          return True

      # If limit is exceeded, wait for 1 seconds before checking again
      time.sleep(1)
