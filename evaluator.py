import utils
import retriever


def evaluate(text_need_evaluated:str, search_results:str)->str:
  prompt = f"""
  Here is the text that needs to be evaluated:
  <text_need_evaluated>
  {text_need_evaluated}
  </text_need_evaluated>

  To determine if the text is verifiable and Fact or Fiction:

  First, identify the key factual claim(s) made in the text. 
  Disregard any statements of opinion.

  Next, carefully review the search results, looking for information relevant to the key claim(s). 
  For each search result, pull out any quotes or facts that either support or refute the claim. 
  Make note of the specific source for each piece of evidence.
  Use as many links in the search results as possible to support your analysis.

  Based on the evidence found (or lack thereof), decide if the key claim is verifiable. 
  If no solid supporting or refuting evidence is found in the search results, the claim is unverifiable.

  If the claim is verifiable, weigh the evidence to determine if it is Fact or Fiction. 
  If there is more supporting evidence, it is likely Fact. If there is more refuting evidence, it is likely Fiction. 
  If the evidence is mixed, use your judgment to decide if it leans Fact or Fiction.

  Finally, write out your analysis using the following format:
  ```
  <Answer>
    <Verifiable>
    Yes/No 
    </Verifiable>

    <Truth or Fiction>
    Truth/Fiction
    </Truth or Fiction>

    <Sources>
      <Supporting>
        1.[Supporting quote/fact](https://...)
        2.[Supporting quote/fact](https://...)
        ...
      </Supporting>
      <Refuting>
        1.[Refuting quote/fact](https://...)
        2.[Refuting quote/fact](https://...)
        ...
      </Refuting>
    </Sources>

    <Explanation>
    Summarize the key evidence and reasoning for your determination of verifiable/unverifiable and Truth/Fiction. Cite the relevant sources and quotes.
    </Explanation>
  </Answer>
  ```
  Your final answer should be wrapped in <Answer> tags.

  Remember, base your determination solely on the information provided in the search results. 
  Do not use any outside knowledge. 
  If the search results are not sufficient to verify the claim, say the claim is unverifiable rather than guessing. 
  Justify your reasoning by directly citing quotes and sources.
  """
  return retriever.retrieve(prompt, search_results, utils.ProviderType.openai, utils.ModelType.advance_model)