import gpt

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

  `keep the sentence as the current format`, but:
  * replace the pronoun (e.g., it, she, he, they, etc.) to the full name based on the context `in place`.
  * replace the referred subject (e.g., the xx) to the  full name based on the context `in place`.
  * add the implicit part (e.g., change `A did B` to `A did B in/on/at/to/from/with/by/for/of C`)) `in place`.
  """
  return gpt.request(prompt)