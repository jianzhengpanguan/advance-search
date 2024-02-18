import re
import gpt

_PROMPT = """
Read the conversation, identify all the premises, hypothesis and inference.
List them in the format:
Premise:
1.__
2.__
Hypothesis:
1.__
2.__
Inference:
1.__
2.__
The the inferences should be in the format:
Premise -> logical dependencies -> Hypothesis

The logical dependencies should be one of:
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

Use instruct to analyze conversation: """

# Divide the text into chunks of 500 characters, with a 50-character overlap.
# Each chunk can read up to 100 patterns in the text.
_CHUCK_SIZE = 500
_OVERLAP_SIZE = 50
_MAX_NUM_PATTERNS = 100
_PREMISE_PATTERN = r"Premise (\b\d+\b)"
_HYPOTHESIS_PATTERN = r"Hypothesis (\b\d+\b)"

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

def fetch_logics(statement):
  logics = []
  chunks = len(statement) // _CHUCK_SIZE
  for i in range(0, chunks):
    request = _PROMPT+statement[i*_CHUCK_SIZE:(i+1)*_CHUCK_SIZE+_OVERLAP_SIZE]
    raw_text = gpt.request(request)
    raw_logic = {
      "Premise": _fetch_patterns(prefix="Premise", raw_text=raw_text),
      "Hypothesis": _fetch_patterns(prefix="Hypothesis", raw_text=raw_text),
      "Inference": _fetch_patterns(prefix="Inference", raw_text=raw_text),
    }

    # If no premises, skip it.
    if not raw_logic["Premise"]:
      continue

    # GPT might put inference into hypothesis, sanity check and move the inference.
    wrong_hypothesis = [hypothesis for hypothesis in raw_logic["Hypothesis"] if "->" in hypothesis]
    raw_logic["Hypothesis"] = [hypothesis for hypothesis in raw_logic["Hypothesis"] if "->" not in hypothesis]

    # If no hypothesis, skip it.
    if not raw_logic["Hypothesis"]:
      continue

    # Parsing the inferences and replace the premises and hypotheses.
    inferences = []
    inferences.extend(raw_logic["Inference"])
    inferences.extend(wrong_hypothesis)

    # If no inference, skip it.
    if not len(inferences):
      continue

    # GPT might mix hypothesis' and premises' text and indices in the inference.
    # Example: Premises: 1.xx, 2.yy; Hypothesis: 1.zz; Inference: 1. Premise 1 + yy -> Cause and effect -> zz.
    # Keep them in the same 'indices' format.
    # Expected Inference: Premise 1 + Premise 2 -> Cause and effect -> Hypothesis 1.
    for inference in inferences:
      # Find all matched premise and hypothesis in the inference.
      premise_indices = re.findall(_PREMISE_PATTERN, inference)
      hypothesis_indices = re.findall(_HYPOTHESIS_PATTERN, inference)
      # Extract the indices from the premises, replace the index with the exact premise in inference.
      for premise_index in premise_indices:
        premise = raw_logic["Premise"][int(premise_index)-1]
        inference = inference.replace(f"Premise {premise_index}", premise)
      # Extract the indices from the hypotheses, replace the index with the exact hypothese in inference.
      for hypothesis_index in hypothesis_indices:
        hypothesis = raw_logic["Hypothesis"][int(hypothesis_index)-1]
        inference = inference.replace(f"Hypothesis {hypothesis_index}", hypothesis)
      logics.append(inference)

  return logics
