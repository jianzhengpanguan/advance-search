import gpt
import utils

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

def stonealone_question(search: str)-> str:
  prompt = f"""
  Given a search: `{search}`
  Rephrase the search to be a standalone question that can be used by the LLM to search the web for information.
  
   1. Follow up question: How does stable diffusion work?
  Rephrased: Stable diffusion working

  2. Follow up question: What is linear algebra?
  Rephrased: Linear algebra

  3: Analysis of domestic needs in the U.S. that could benefit from increased funding (e.g., healthcare, infrastructure, education).
  Rephrase: Domestic needs in the U.S. benefiting from increased funding

  4: Comparative studies on the effectiveness of funding domestic vs. international environmental projects.
  Rephrased: Effectiveness of funding domestic vs. international environmental projects

  Rephrased standalone question:
  """
  # Currently only openai advance model and anthropic small and advance model are supported.
  return gpt.anthropic_request(prompt, utils.ModelType.small_model)

