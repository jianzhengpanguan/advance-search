import gpt
import searcher

_MAX_ITER = 3

def evaluate(text):
  search_results = searcher.search(text, _MAX_ITER)

  evaluate_request = f"""Verify if {text} is truth or fiction, through the following article: {str(search_results)} Answer in the following way:
  ```
  # Verifiable:
  * Yes/No
  # Truth or Fiction:
  * Truth/Fiction
  # Sources:
  ## Search 1.__
  1. [bullet point](link)
  2. [bullet point](link)
  ## Search 2.__
  1. [bullet point](link)
  2. [bullet point](link)
  ## Explain:
  * __
  * __

  ```
  """
  evaluate_result = gpt.request(evaluate_request)
  return evaluate_result