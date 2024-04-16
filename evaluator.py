import gpt
import searcher



def evaluate(text_need_evaluated, search_results):
  evaluate_request = f"""Verify if {text_need_evaluated} is truth or fiction, through the following article: {str(search_results)} Answer in the following way:
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