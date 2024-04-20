import re
import gpt
import searcher

"""Explanation
Fallacy of Composition: Fallacy of Composition. Assuming that what is true for the individual parts must also be true for the whole.,
Fallacy of Decomposition: Fallacy of Decomposition. Assuming that what is true for the whole must also be true for the individual parts.,
Circular Argument (Begging the Question): Circular Argument. When the conclusion of an argument is assumed in one of the premises.,
Appeal to Ignorance (Argumentum ad Ignorantiam): Appeal to Ignorance. Arguing that a proposition is true because it has not been proven false, or vice versa.,
Atypical Sample: Atypical Sample. Drawing a conclusion about a population based on a sample that is not representative of the population.,
Hasty Generalization: Hasty Generalization. Drawing a conclusion about a population based on a sample that is too small.,
Randomly Assign Cause and Effect (Post Hoc Ergo Propter Hoc): Randomly Assign Cause and Effect. Assuming that because one event follows another, the first event must have caused the second.,
Slippery Slope Fallacy: Slippery Slope Fallacy. Arguing that a relatively small first step will lead to a chain of related events resulting in some significant impact.,
Fallacy of Excluded Middle (False Dichotomy): Fallacy of Excluded Middle. Assuming that there are only two mutually exclusive outcomes when there are actually more options.,
Vague Meaning (Equivocation): Vague Meaning. Using a term with multiple meanings in different parts of an argument as if it has a single meaning throughout.,
Modify Definition (Moving the Goalposts): Modify Definition. Changing the definition of a term within an argument to suit the conclusion.,
Appeal to the Crowd (Argumentum ad Populum): Appeal to the Crowd. Arguing that a proposition is true because many or most people believe it.,
Guilty Association (Association Fallacy): Guilty Association. Assuming that because two things share a property, they are the same in other respects.,
Appeal to Emotion (Argumentum ad Passiones): Appeal to Emotion. Attempting to persuade using an emotional response instead of a valid argument.,
Appeal to Consequences (Argumentum ad Consequentiam): Appeal to Consequences. Arguing that a proposition is true or false based on the desirability of its consequences.,
Straw Man Fallacy: Straw Man Fallacy. Misrepresenting an opponent's argument to make it easier to attack.,
Origin Fallacy (Genetic Fallacy): Origin Fallacy. Judging the value or truth of a belief based on its origin or history.,
Personal Attacks (Ad Hominem): Personal Attacks. Attacking the person making the argument rather than the argument itself.,
Resort to Hypocrisy (Tu Quoque): Resort to Hypocrisy. Discrediting an opponent's argument by pointing out their failure to act consistently with the argument's conclusion.,
Appeal to Irrelevant Authority (Argumentum ad Verecundiam): Appeal to Irrelevant Authority. Arguing that a proposition is true because an authority figure says it is, even though the authority is not an expert in the field.,
Affirmative Consequent (Affirming the Consequent): Affirmative Consequent. Assuming that if P implies Q and Q is true, then P must be true (a form of invalid argument in logic).
Non Sequitur: Non Sequitur is a logical fallacy where the conclusion does not logically follow from the premises. In other words, there is a disconnect between the premises and the conclusion, making the argument invalid. This fallacy occurs when the conclusion is not a natural or logical outcome of the arguments presented, often resulting in a statement or conclusion that seems out of place or irrelevant to the preceding discussion. Non sequiturs can arise from faulty reasoning, misplaced connections, or irrelevant information being introduced into the argument.
"""

_PROMPT = """
Read the inference, identify all the fallacies and explain why is it a fallacy.
List them in the format:
```
Fallacy:
1.__
...

Explanation:
1.__
...
```

The fallacies should be one of:
1. Fallacy of Composition
2. Fallacy of Decomposition
3. Circular Argument (Begging the Question)
4. Appeal to Ignorance (Argumentum ad Ignorantiam)
5. Atypical Sample
6. Hasty Generalization
7. Randomly Assign Cause and Effect (Post Hoc Ergo Propter Hoc)
8. Slippery Slope Fallacy
9. Fallacy of Excluded Middle (False Dichotomy)
10. Vague Meaning (Equivocation)
11. Modify Definition (Moving the Goalposts)
12. Appeal to the Crowd (Argumentum ad Populum)
13. Guilty Association (Association Fallacy)
14. Appeal to Emotion (Argumentum ad Passiones)
15. Appeal to Consequences (Argumentum ad Consequentiam)
16. Straw Man Fallacy
17. Origin Fallacy (Genetic Fallacy)
18. Personal Attacks (Ad Hominem)
19. Resort to Hypocrisy (Tu Quoque)
20. Appeal to Irrelevant Authority (Argumentum ad Verecundiam)
21. Affirmative Consequent (Affirming the Consequent)
22. Non Sequitur (does not follow)

Use instruct to analyze inference: 
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


def _to_fallacy_explanation(inference):
  request = _PROMPT+inference
  return gpt.request(request)

def find_fallacies(inferences:list)->list:
  fallacies = []
  for inference in inferences:
    inference = f"Inference: Premises->Hypothesis {str(inference)}"
    fallacy_explanation = _to_fallacy_explanation(inference)
    raw = {
      "Fallacy": _fetch_patterns(prefix="Fallacy", raw_text=fallacy_explanation),
      "Explanation": _fetch_patterns(prefix="Explanation", raw_text=fallacy_explanation),
    }
    explanation_searches = {}
    for explanation in raw["Explanation"]:
      if explanation:
        explanation_searches[explanation] = searcher.search(explanation, _MAX_ITER)
    fallacies.append({
      "Inference": inference,
      "Fallacy": [fallacy for fallacy in raw["Fallacy"] if fallacy],
      "Explanation": explanation_searches,
    })
  return fallacies

