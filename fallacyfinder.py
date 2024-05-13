import re
import gpt
import json
import utils
import searcher

_JSON_OUTPUT = """
Response in the json format: 
```json
[
  {"1.fallacy": "1.explanation"},
  {"2.fallacy": "2.explanation"},
]
```
"""
# TODO: Currently JSON output format is not stable in LLM (e.g., GPT 4.0, Claude 3).
# Once LLM correctly constantly support json format, remove the text output.
_TEXT_OUTPUT = """
Response in the following format:
```
Fallacy:
1.__
...
Explanation:
1.__
...
```
"""
_PROMPT_TEMPLATE = """
Read the inference, identify all the fallacies.
For each fallacy, explain why the inference is that fallacy.
%s

The fallacies should be one or few of the following:
```
{
  "Fallacy of Composition": "Fallacy of Composition. Assuming that what is true for the individual parts must also be true for the whole.",
  "Fallacy of Decomposition": "Fallacy of Decomposition. Assuming that what is true for the whole must also be true for the individual parts.",
  "Circular Argument (Begging the Question)": "Circular Argument. When the conclusion of an argument is assumed in one of the premises.",
  "Appeal to Ignorance (Argumentum ad Ignorantiam)": "Appeal to Ignorance. Arguing that a proposition is true because it has not been proven false, or vice versa.",
  "Atypical Sample": "Atypical Sample. Drawing a conclusion about a population based on a sample that is not representative of the population.",
  "Hasty Generalization": "Hasty Generalization. Drawing a conclusion about a population based on a sample that is too small.",
  "Randomly Assign Cause and Effect (Post Hoc Ergo Propter Hoc)": "Randomly Assign Cause and Effect. Assuming that because one event follows another, the first event must have caused the second.",
  "Slippery Slope Fallacy": "Slippery Slope Fallacy. Arguing that a relatively small first step will lead to a chain of related events resulting in some significant impact.",
  "Fallacy of Excluded Middle (False Dichotomy)": "Fallacy of Excluded Middle. Assuming that there are only two mutually exclusive outcomes when there are actually more options.",
  "Vague Meaning (Equivocation)": "Vague Meaning. Using a term with multiple meanings in different parts of an argument as if it has a single meaning throughout.",
  "Modify Definition (Moving the Goalposts)": "Modify Definition. Changing the definition of a term within an argument to suit the conclusion.",
  "Appeal to the Crowd (Argumentum ad Populum)": "Appeal to the Crowd. Arguing that a proposition is true because many or most people believe it.",
  "Guilty Association (Association Fallacy)": "Guilty Association. Assuming that because two things share a property, they are the same in other respects.",
  "Appeal to Emotion (Argumentum ad Passiones)": "Appeal to Emotion. Attempting to persuade using an emotional response instead of a valid argument.",
  "Appeal to Consequences (Argumentum ad Consequentiam)": "Appeal to Consequences. Arguing that a proposition is true or false based on the desirability of its consequences.",
  "Straw Man Fallacy": "Straw Man Fallacy. Misrepresenting an opponent's argument to make it easier to attack.",
  "Origin Fallacy (Genetic Fallacy)": "Origin Fallacy. Judging the value or truth of a belief based on its origin or history.",
  "Personal Attacks (Ad Hominem)": "Personal Attacks. Attacking the person making the argument rather than the argument itself.",
  "Resort to Hypocrisy (Tu Quoque)": "Resort to Hypocrisy. Discrediting an opponent's argument by pointing out their failure to act consistently with the argument's conclusion.",
  "Appeal to Irrelevant Authority (Argumentum ad Verecundiam)": "Appeal to Irrelevant Authority. Arguing that a proposition is true because an authority figure says it is, even though the authority is not an expert in the field.",
  "Affirmative Consequent (Affirming the Consequent)": "Affirmative Consequent. Assuming that if P implies Q and Q is true, then P must be true (a form of invalid argument in logic).",
  "Non Sequitur": "Non Sequitur is a logical fallacy where the conclusion does not logically follow from the premises. In other words, there is a disconnect between the premises and the conclusion, making the argument invalid. This fallacy occurs when the conclusion is not a natural or logical outcome of the arguments presented, often resulting in a statement or conclusion that seems out of place or irrelevant to the preceding discussion. Non sequiturs can arise from faulty reasoning, misplaced connections, or irrelevant information being introduced into the argument.",
}
```
Use instruct to analyze inference: 
%s
"""
_MAX_NUM_PATTERNS = 100
_MAX_ITER = 3

# Fetch the patterns in fallacy, explanation.
# Example raw text: r"Fallacy:\s*\n(1\..*?)\n(2\..*?)\n".
def _fetch_patterns(prefix, raw_text, max_iter=_MAX_NUM_PATTERNS)-> list[str]:
  patterns = []
  pattern = prefix+r":\s*\n"
  for i in range(1, max_iter):
    pattern += f"({i}"+r"\..*?)\n"
    # Find all matched content.
    matches = re.search(pattern, raw_text, re.DOTALL)
    if matches == None:
      return patterns
    patterns.append(matches.group(i).strip())
  return patterns


def _to_fallacy_explanations(inference:str)->dict[str, str]:
  fallacy_explanations = {}
  request = _PROMPT_TEMPLATE % (_JSON_OUTPUT, inference)
  response = gpt.openai_request(request, utils.ModelType.advance_model)
  # Find json part in ```json * ```.
  # The json part is a list of dictionary {fallacy:explanation}.
  json_part = re.findall(r"[\`{3}json].*[\`{3}]", response, re.DOTALL)
  if json_part:
    for part in json_part:
      if part:
        parsed_part = part.split("```json")[-1].split("```")[0]
        for fallacy_explanation in json.loads(parsed_part):
          for fallacy, explanation in fallacy_explanation.items():
            fallacy_explanations[fallacy] = explanation
  
  # If LLM does not support Json format , use the text format.
  request = _PROMPT_TEMPLATE % (_TEXT_OUTPUT, inference)
  response = gpt.openai_request(request, utils.ModelType.advance_model)
  fallacies = _fetch_patterns(prefix="Fallacy", raw_text=response)
  explanations = _fetch_patterns(prefix="Explanation", raw_text=response)
  num_fallacies = min(len(fallacies), len(explanations))
  for i in range(num_fallacies):
    fallacy_explanations[fallacies[i]] = explanations[i]
  return fallacy_explanations

class FallacySearches:
  def __init__(self, fallacy:str, explanation:str, search_results:list[searcher.SearchResults]):
    self.fallacy = fallacy
    self.explanation = explanation
    self.search_results = search_results

  def __str__(self):
    return f"Fallacy: {self.fallacy}\nExplanation: {self.explanation}\nSearch Results: {self.search_results}\n"

  def to_dict(self):
    return {
      "fallacy": self.fallacy,
      "explanation": self.explanation,
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

def _search_to_avoid_fallacies(inference:str)->list[FallacySearches]:
  fallacy_searches:list[FallacySearches] = []
  fallacy_explanations = _to_fallacy_explanations(inference)
  
  for fallacy, explanation in fallacy_explanations.items():
    topic = f"""
    ```
    Given: `{inference}`,
    The inference commits the fallacy of `{fallacy}`,
    because: `{explanation}`
    ```
    """
    search_results = searcher.search(topic, _MAX_ITER, utils.SearchType.fallacy_avoider)
    fallacy_searches.append(FallacySearches(fallacy, explanation, search_results))

  return fallacy_searches

def find(inferences:list)->dict[str, list[FallacySearches]]:
  inference_fallacies:dict[str, list[FallacySearches]] = {}
  for inference in inferences:
    inference = f"Inference=Premises->Hypothesis: {inference}"
    inference_fallacies[inference] = _search_to_avoid_fallacies(inference)
    return inference_fallacies
  return inference_fallacies

