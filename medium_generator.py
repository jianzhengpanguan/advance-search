import argparse
import gpt
import utils
import re
from applog import logger as logging

_MAX_ITER = 3

def main():
    parser = argparse.ArgumentParser(description='Process the flags.')
    parser.add_argument('-folder', '--folder_path', type=str, default='./data/5. Taylor Swift relationship with NFL player Travis Kelce is part of a Democratic plot to sway the upcoming election/2', help='Folder path')
    args = parser.parse_args()
    folder_path = args.folder_path
    raw_file_path = f'{folder_path}/raw.txt'
    logics_file_path = f'{folder_path}/logics.txt'
    evaluation_file_path = f'{folder_path}/evaluation.txt'
    fallacy_file_path = f'{folder_path}/fallacy.txt'
    fallacy_evaluation_file_path = f'{folder_path}/fallacy_evaluation.txt'
    meduim_file_path = f'{folder_path}/meduim.txt'

    print(f"Raw file path: {raw_file_path}")
    print(f"Logics file path: {logics_file_path}")
    print(f"Evaluation file path: {evaluation_file_path}")
    print(f"Fallacy file path: {fallacy_file_path}")
    print(f"Fallacy evaluation file path: {fallacy_evaluation_file_path}")

    with open(raw_file_path, "r", encoding='utf-8') as f:
      raw = f.read()
    
    with open(logics_file_path, "r", encoding='utf-8') as f:
      logics = f.read()

    with open(evaluation_file_path, "r", encoding='utf-8') as f:
      evaluation = f.read()
    
    with open(fallacy_file_path, "r", encoding='utf-8') as f:
      fallacy = f.read()

    with open(fallacy_evaluation_file_path, "r", encoding='utf-8') as f:
      fallacy_evaluation = f.read()

    pattern = r'<Verifiable>\s*(Yes|No)\s*</Verifiable>'

    fallacy_premises_hypothese = []
    fallacy_evaluations = []
    for fallacy_eval in fallacy_evaluation.split("Premise/Hypothesis:"):
      if "<verifiable>" not in fallacy_eval.lower():
        continue
      match = re.search(pattern, fallacy_eval, re.IGNORECASE)
      if not match:
        continue
      if match.group(1).lower() == "yes":
        fallacy_premises_hypothese.append(fallacy_eval.split("\n")[0])
        fallacy_evaluations.append(fallacy_eval)

    prompt_writing = f"""
    You are an expert for Meduim blog writing. 

    You are given a raw txt, but the raw text needed to be evaluated, 
    because the raw text might be "radical views" or "extreme opinions" expressed by influencers, 
    often accompanied by "partial facts" or "misinformation."
    <raw>
    {raw}
    </raw>

    In this case, you are given an inference extract from the raw text.
    An inference contains premises and hypotheses.
    <inference>
    {logics}
    </inference>
  
    You are then given the premises evaluation, evaluating if each premise is verifiable truth or fiction.
    <evaluation>
    {evaluation}
    </evaluation>

    Now write the blog step by step:
    1. Generate the topic
    ```
    The topic should like `Is xxx fact or fiction?`
    ```

    2. Check the rational
    ```
    * Summerize the raw text.
    * Discuss the hypothesis.
    * Mentioned we will check the rationale and logic chain in next section.
    ```

    3. Logic Chain Analysis
    ```
    * List each premise, 
    * Explain why it related to hypothesis.
    ```

    4. Evaluating Premises’ Veracity
    Convert the evaluation of each premise into the following format:
    ```
    Here is an analysis of the veracity of each premise in logic chain of ... 

    Premise 1: ...
    Verifiable: Yes/No
    Truth or Fiction: Fiction
    Explanation: ...
    Source: 
    1. https://...
    ...

    In summary, ... out of the ... premises (...%) in ... logic chain are classified as truthful based on the available evidence, while ... premises (...%) are deemed to be fiction or lacking substantive proof. This suggests that the rationale ....
    ```
    """

    prompt_continuesly_writing = f"""
    You are an expert for Meduim blog writing. 
    Here is the blog:
    <blog>
    %s
    </blog>
    Help me continiously write the blog.

    You are given the fallacies in the inference.
    <fallacy>
    {fallacy}
    </fallacy>

    A fallacy can be solved by new premises/hypotheses.
    <fallacy_premises_hypothese>
    {fallacy_premises_hypothese}
    </fallacy_premises_hypothese>

    You are given the fallacies evaluation, evaluating if each premises/hypothese is verifiable truth or fiction.
    <fallacy_evaluation>
    {fallacy_evaluations}
    </fallacy_evaluation>

    Now continuesly write the blog step by step:
    1. Logical Fallacies in Rationale
    ```
    To avoid this fallacy, the logic chain would need to include additional premises that provide a more balanced and comprehensive assessment.
    List all fallacies and premises
    ```

    2. Evaluating Additional Premises/hypothese’ Veracity
    Convert the evaluation of each premise into the following format:
    ```
    Here is an analysis of the veracity of each premise in logic chain of ... 

    Premise 1: ...
    Verifiable: Yes/No
    Truth or Fiction: Fiction
    Explanation: ...
    Source: 
    1. https://...
    ...

    In summary, ... out of the ... premises (...) in ... logic chain are classified as truthful based on the available evidence, while ... premises (...) are deemed to be fiction or lacking substantive proof. This suggests that the rationale ....
    ```

    3. Summary
    Summarize and the doc into the following format:
    ```
    ... was based on a logic chain that ...
    The rationale relied on premises such as ...

    However, an analysis of the logic chain reveals the presence of the ... fallacy ...
    To address this fallacy, ... additional premises were introduced: ...

    The original logic chain had a truthfulness rate of ..., while the revised logic chain achieves a truthfulness rate of ...
    +--------------------------------+-------------------+
    | Premise Set                    | Truthfulness Rate |
    |--------------------------------|-------------------|
    | Original Premises (...)        | ...               |  
    | With Additional Premises (...) | ...               |
    +--------------------------------+-------------------+

    The final hypotheses truthfulness:
    For Hypothesis 1: ... There are ... Supporting ... Refuting, so it is ... Fact/Fiction.
    ...
    ```
    """

    # Step 1: Initial
    blog = gpt.openai_request(prompt_writing, utils.ModelType.advance_model)
    continues_blog = gpt.openai_request(prompt_continuesly_writing % (blog), utils.ModelType.advance_model)

    with open(meduim_file_path, "w", encoding='utf-8') as f:
      f.write(blog)
      f.write(continues_blog)


if __name__ == "__main__":
    main()
