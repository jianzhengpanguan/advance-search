import re
import gpt
import json
import utils
import searcher
import rephraser
from applog import logger as logging

_MAX_ITER = 1

_HYPOTHESIS_PROMPT = """
Here is an inference:

<inference>
%s
</inference>

This inference commits the following fallacy:

<fallacy>
%s
</fallacy>

The explanation for why it commits this fallacy is:

<fallacy_explanation>
%s
</fallacy_explanation>

Think through the inference carefully in light of the identified fallacy and explanation. 
How could the hypothesis be modified to avoid committing the fallacy?

<fix_instructions>
Provide clear, step-by-step instructions for how to modify the inference to fix the fallacy and make the argument logically valid.
Export the rephrased hypothesis and why rephrasing as the following JSON object.
</fix_instructions>

```json
[
  {
    "hypothesis": ___,
    "why": ___
  },
  {
    "hypothesis": ___,
    "why": ___
  }
]
```
"""

_PREMISE_PROMPT = """
Here is an inference:

<inference>
%s
</inference>

This inference commits the following fallacy:

<fallacy>
%s
</fallacy>

The explanation for why it commits this fallacy is:

<fallacy_explanation>
%s
</fallacy_explanation>

Think through the inference carefully in light of the identified fallacy and explanation. 
How could the premises be modified to avoid committing the fallacy? 
Are additional premises needed, or do existing premises need to be qualified or changed? 

<fix_instructions>
Provide clear, step-by-step instructions for how to modify the inference to fix the fallacy and make the argument logically valid. 
Be specific about what premises to add, remove, or change. 
Provide guidance on adding qualifiers or narrowing the scope of claims as appropriate to align premises with hypothesis and avoid hasty generalizations.
Export the "rephrased"/"adding new premises" and why "adding new" or "rephrasing" premises as the following JSON object.
</fix_instructions>

```json
[
  {
    "premise": ___,
    "why": ___
  },
  {
    "premise": ___,
    "why": ___
  }
]
```
"""
def _suggest_search_reason(inference:str, fallacy:str, explanation:str)->dict[str, str]:
  topic_explanations:dict[str, str] = {}
  for prompt in [_PREMISE_PROMPT, _HYPOTHESIS_PROMPT]:
    response = gpt.openai_request(prompt % (inference, fallacy, explanation), utils.ModelType.advance_model)

    # Find json part in ```json * ```.
    # The json part is a list of dictionary {fallacy:explanation}.
    json_obj = rephraser.best_effort_json(response)
    if not json_obj:
      continue

    topic, explanation = "", ""
    for topic_explanation in json_obj:
      if "premise" in topic_explanation:
        topic = topic_explanation["premise"]
      if "hypothesis" in topic_explanation:
        topic = topic_explanation["hypothesis"]
      if "why" in topic_explanation:
        explanation = topic_explanation["why"]
      topic_explanations[topic] = explanation
      

  return topic_explanations


class FallacySearches:
  def __init__(self, fallacy:str, fallacy_explanation:str, search:str, search_reason:str, search_results:list[searcher.SearchResults]):
    self.fallacy = fallacy
    self.fallacy_explanation = fallacy_explanation
    self.search = search
    self.search_reason = search_reason
    self.search_results = search_results

  def __str__(self):
    return f"""
      Fallacy: {self.fallacy}
      Explanation: {self.fallacy_explanation}
      Search: {self.search}
      Search Reason:{self.search_reason}
      Search Results: {self.search_results}
    """

  def to_dict(self):
    return {
      "fallacy": self.fallacy,
      "explanation": self.fallacy_explanation,
      "search": self.search,
      "search_reason": self.search_reason,
      "search_results": self.search_results
    }

class CustomEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, FallacySearches):
      return obj.to_dict()
    if isinstance(obj, searcher.SearchResults):
      return obj.to_dict()
    # If the object is of any other type, use the default behavior
    return json.JSONEncoder.default(self, obj)

def _search_to_avoid_fallacies(inference:str, fallacy:str, fallacy_explanation:str)->list[FallacySearches]:
  fallacySearches:list[FallacySearches] = []
  search_reasons = _suggest_search_reason(inference, fallacy, fallacy_explanation)
  for search, search_reason in search_reasons.items():
    search_results = searcher.search(search, _MAX_ITER)
    fallacySearches.append(FallacySearches(fallacy, fallacy_explanation, search, search_reason, search_results))
  return fallacySearches

def solve(inference_fallacies:dict[str, dict[str, str]])->dict[str, list[FallacySearches]]:
  inference_searches:dict[str, list[FallacySearches]] = {}
  for inference in inference_fallacies:
    fallacy_searches:list[FallacySearches] = []
    for fallacy, explanation in inference_fallacies[inference].items():
      fallacy_searches.extend(_search_to_avoid_fallacies(inference, fallacy, explanation))
    inference_searches[inference] = fallacy_searches
  return inference_searches