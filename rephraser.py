import gpt
import utils
import re
import json
from applog import logger as logging

# Use context to replace ambiguous terms in an inference.
# An inference can be ambiguous, when:
# 1. Use prenoun as subject, e.g., it, she, he, etc.
# 2. Refer to a specific noun, e.g., the xx.
# 3. Miss implicit element, e.g., A did B (for/with/to/... C).
# Example:
# ```
# 1. The United States' participation in the Paris accord is bad for the country's economy
# +
# 4. President Trump has stated the intention to withdraw from the international agreement. 
# + 
# 5. He is open to renegotiation if it can lead to a deal that is fair. 
# -> Causation -> 
# 2. There is a possibility for a new and fairer agreement through renegotiation.
# ```
# Analysis:
# The premise `He is open to renegotiation if it can lead to a deal that is fair.` is ambiguous, because: 
# * `He` should be `President Trump`
# * `it` should be `renegotiation of the international agreement`, more specifically, `renegotiation of the Paris accord`.
# * `lead to a deal that is fair` should be `lead to a deal that is fair for the United States`
def replace_ambiguous_terms(inference: str)-> str:
  prompt = f"""
  Given a sentence:
  {inference}

  Export in the json format like:
  ```json
  ...
  ```
  but:
  * replace the pronoun (e.g., it, she, he, they, etc.) to the full name based on the context `in place`.
  * replace the referred subject (e.g., the xx) to the  full name based on the context `in place`.
  * add the implicit part (e.g., change `A did B` to `A did B in/on/at/to/from/with/by/for/of C`)) `in place`.
  """
  # Currently only openai advance model and anthropic small and advance model are supported.
  return gpt.anthropic_request(prompt, utils.ModelType.small_model)

def _to_json_text(text:str)->str:
  json_part = re.findall(r"[\`{3}json].*[\`{3}]", text, re.DOTALL)
  if not json_part or not json_part[0]:
    logging.warning(f"Does not contain json: {text}")
    return ""
  return json_part[0].split("```json")[-1].split("```")[0]
  

def best_effort_json(text:str):
  json_text = _to_json_text(text)
  if not json_text:
    return None
  json_obj = None
  try:
    json_obj = json.loads(json_text)
  except json.JSONDecodeError as e:
    logging.error(f"Failed to parse json: {e}\n text: {text}")
    prompt = f"""
    Fix the json format file:
    ```json
    {json_text}
    ```
    Export in the json format like:
    ```json
    ...
    ```
    """
    # Currently only openai advance model and anthropic small and advance model are supported.
    best_effort_text = gpt.anthropic_request(prompt, utils.ModelType.small_model)
    best_effort_json_text = _to_json_text(best_effort_text)
    try:
      json_obj = json.loads(best_effort_json_text)
    except json.JSONDecodeError as e:
      logging.error(f"Failed to parse json: {e}\n best effort text: {best_effort_text}")
      return None
  return json_obj

def stonealone_question(search: str)-> str:
  prompt = f"""
  Rephrase the search to be a standalone question that can be used by the LLM to search the web for information.
  
  Examples:
  1. Question: `How does stable diffusion work?`
  Rephrased: `Stable diffusion working`

  2. Question: `What is linear algebra?`
  Rephrased: `Linear algebra`

  Now apply to:
  Question: `{search}`
  Rephrased:
  """
  return gpt.anthropic_request(prompt, utils.ModelType.advance_model).replace("`", "").replace("\"", "").split(":")[-1].strip()

