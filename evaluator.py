import gpt
import searcher

_MAX_ITER = 3

def evaluate(text):
  search_results = searcher.search(text, _MAX_ITER)

  evaluate_request = f"""Verify {text} through the following article: {str(search_results)} Answer in the following way:
  Yes/No
  The information obtained from the article you provided is as follows:
  1. [bullet point](link)
  2. [bullet point](link)

  """
  evaluate_result = gpt.request(evaluate_request)
  return evaluate_result