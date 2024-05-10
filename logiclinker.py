import re
import gpt
import rephraser
import utils
import json
from applog import logger as logging

_JSON_OUTPUT = """
Response in the json format:
```json
{
  "Premise": [
    "1.__",
    "2.__"
  ],
  "Hypothesis": [
    "1.__",
    "2.__"
  ],
  "Inference": [
    {
      "Premise Index": [
        "1",
        ...
      ],
      "Hypothesis Index": [
        "1",
        ...
      ],
      "logical dependency": "__"
    },
    {
      ...
    },
  ]
}
```
"""
# TODO: Currently JSON output format is not stable in LLM (e.g., GPT 4.0, Claude 3).
# Once LLM correctly constantly support json format, remove the text output.
_TEXT_OUTPUT = """
Response in the following format:
```
Premise:
1.__
2.__
Hypothesis:
1.__
2.__
Inference:
1.Premise:[1+2+3...] -> logical dependencies -> Hypothesis:[1+2+3...]
2.Premise:[1+2+3...] -> logical dependencies -> Hypothesis:[1+2+3...]
```
"""
_PROMPT_TEMPLATE = """
Read the conversation, identify all the premises, hypothesis and inference.
%s

Notice:
* Deduplicate the same premise, hypothesis or inference.
* In inference, only show the indices of premise and hypothesis.
* The logical dependencies should be one of:
1. Cause and effect
2. Spatial relationship
3. Temporal relationship
4. Comparison
5. Generalization
6. Probability
7. Association
8. Causation
9. Contrast
Repeat to list all the inferences in the conversation.

Use instruct to analyze conversation: 
%s
"""

# Divide the text into chunks of 500 characters, with a 50-character overlap.
# Each chunk can read up to 100 patterns in the text.
_CHUCK_SIZE = 500
_OVERLAP_SIZE = 50
_MAX_NUM_PATTERNS = 100

# Fetch the patterns in premise, hypothesis.
# Example raw text: r"Premise:\s*\n(1\..*?)\n(2\..*?)\n".
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

def _raw_text_to_logics(raw_text:str, provider_type:utils.ProviderType=utils.ProviderType.openai, model_type:utils.ModelType=utils.ModelType.advance_model)->list[{dict[str,list[str]]}]:
  logics:list[{dict[str,list[str]]}] = []
  raw_logic = {
    "Premise": _fetch_patterns(prefix="Premise", raw_text=raw_text),
    "Hypothesis": _fetch_patterns(prefix="Hypothesis", raw_text=raw_text),
    "Inference": _fetch_patterns(prefix="Inference", raw_text=raw_text),
  }

  # If no premises, skip it.
  if not raw_logic["Premise"]:
    return logics

  # GPT might put inference into hypothesis, sanity check and move the inference.
  wrong_hypothesis = [hypothesis for hypothesis in raw_logic["Hypothesis"] if "->" in hypothesis]
  raw_logic["Hypothesis"] = [hypothesis for hypothesis in raw_logic["Hypothesis"] if "->" not in hypothesis]

  # If no hypothesis, skip it.
  if not raw_logic["Hypothesis"]:
    return logics

  # Parsing the inferences and replace the premises and hypotheses.
  inferences = []
  inferences.extend(raw_logic["Inference"])
  inferences.extend(wrong_hypothesis)

  # If no inference, skip it.
  if not len(inferences):
    return logics

  # GPT should enforce hypotheses and premises keeping indices format in the inference.
  # Replace the indices to the content, example Inference: Premise 1 + Premise 2 -> Hypothesis 1.
  for inference in inferences:
    if "->" not in inference:
      continue
    logging.info(f"Inference before parsing: {inference}")
    premise_str, hypothesis_str = inference.split("->")[0], inference.split("->")[-1]
    # Ignore the index number before Premise.
    # Example： 1. Premise[2,3], we should skip the 1 and keep the 2 and 3.
    premise_str = premise_str.split("Premise")[-1]
    # Find all premise and hypothesis indices in the inference.
    premise_indices = re.findall(r"\d+", premise_str)
    hypothesis_indices = re.findall(r"\d+", hypothesis_str)
    if not premise_indices or not hypothesis_indices:
      continue
    # Extract the indices from the premises/hypotheses, replace the index with the exact premise/hypothesis in inference.
    premises = [raw_logic["Premise"][int(premise_index)-1] for premise_index in premise_indices if int(premise_index)-1 < len(raw_logic["Premise"])]
    hypotheses = [raw_logic["Hypothesis"][int(hypothesis_index)-1] for hypothesis_index in hypothesis_indices if int(hypothesis_index)-1 < len(raw_logic["Hypothesis"])]
    logics.append({"premises": premises, "hypothesis": hypotheses})
  return logics

def _json_text_to_logics(raw_json:str)->list[{dict[str,list[str]]}]:
  logics:list[{dict[str,list[str]]}] = []
  # Find json part in ```json * ```.
  # The json part is a list of dictionary {fallacy:explanation}.
  json_part = re.findall(r"[\`{3}json].*[\`{3}]", raw_json, re.DOTALL)
  if not json_part:
    return logics
  raw_logic = {}
  for part in json_part:
    if part:
      parsed_part = part.split("```json")[-1].split("```")[0]
      raw_logic = json.loads(parsed_part)

  # If no premises, hypothesis or inferences, skip it.
  for key in ["Premise", "Hypothesis","Inference"]:
    if not key in raw_logic:
      return logics
  for inference in raw_logic["Inference"]:
    # If no premises, hypothesis in the inference, skip it.
    if not inference["Premise Index"] or not inference["Hypothesis Index"]:
      continue
    premise_indices = inference["Premise Index"]
    hypothesis_indices = inference["Hypothesis Index"]
    # Extract the indices from the premises/hypotheses, replace the index with the exact premise/hypothesis in inference.
    premises = [raw_logic["Premise"][int(premise_index)-1] for premise_index in premise_indices if int(premise_index)-1 < len(raw_logic["Premise"])]
    hypotheses = [raw_logic["Hypothesis"][int(hypothesis_index)-1] for hypothesis_index in hypothesis_indices if int(hypothesis_index)-1 < len(raw_logic["Hypothesis"])]
    logics.append({"premises": premises, "hypothesis": hypotheses})
  return logics

def fetch_logics(statement:str, provider_type:utils.ProviderType=utils.ProviderType.openai, model_type:utils.ModelType=utils.ModelType.advance_model):
  logics:list[{dict[str,list[str]]}] = []
  chunks = gpt.divide_statement(statement)
  for current_chunk in chunks:
    request = _PROMPT_TEMPLATE % (_JSON_OUTPUT, current_chunk)
    raw_json = gpt.request(request, provider_type, model_type)
    json_logics = None
    try:
      json_logics = _json_text_to_logics(raw_json)
    except Exception as e:
      logging.error(f"LLM does not support Json format: {e}")
    # If LLM support Json format, add it into logics.
    if json_logics:
      logics.extend(json_logics)
      continue
    
    # If LLM does not support Json format, use the text format.
    request = _PROMPT_TEMPLATE % (_TEXT_OUTPUT, current_chunk)
    raw_text = gpt.request(request, provider_type, model_type)
    logics.extend(_raw_text_to_logics(raw_text))
  
  # Replace Ambiguous Terms.
  for i, logic in enumerate(logics):
    json_str = json.dumps(logic)
    output = rephraser.replace_ambiguous_terms(json_str, provider_type, model_type)
    try:
      logics[i] = json.loads(output.split("```json")[-1].split("```")[0])
    except Exception as e:
      logging.warning(f"json loads failure: {e}")
  return logics
