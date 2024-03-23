# Advance Search

## Overview

The Advance Search project aims to develop a program that leverages Large Language Models (LLMs) to search, evaluate, and summarize opinions and facts, especially in the context of the increasing prevalence of "radical views" or "extreme opinions" expressed by influencers, often accompanied by "partial facts" or "misinformation."

## Installation

### Step 1: Download and Install

Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/jianzhengpanguan/advance-search.git
cd advance-search
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Configuration

Update the `config.ini` file with your API key and model ID (change the url if you want to use other search enginee and llm):

```
[SEARCH]
api_key = fake_key
cx = fake_customer_search_id
url = https://www.googleapis.com/customsearch/v1


[LLM]
api_key = fake_key
url = https://api.openai.com/v1/chat/completions
model = gpt-4-1106-preview
```

## Usage

### Step 1: Run the Program

Execute the program from the command line:

```bash
python main.py
```

### Step 2: Input Data

Provide the path to the file containing questions or statements using the `--raw_file_path` flag (default path is `./data/raw.txt`):

```bash
python main.py --raw_file_path ./path/to/your/file.txt
```

### Step 3: Review Results

Check the summarized results and evaluations in the output files located in the `./data/` directory:

- `logics.txt`: Contains the logical analysis of the input data.
- `fallacy.txt`: Provides a list of fallacies identified in the input data.
- `evaluation.txt`: Provides an evaluation summary of the opinions and facts.

## Example outputs:
More details in `./data/` directory, here shows paritial results:
- `logics.txt`: 
```
...
3. Mr. Trump listed sectors of the United States economy that would lose revenue and jobs if the country remained part of the accord. + 2. A study asserts that the agreement would cost 2.7 million jobs by 2025, which is disputed by environmental groups. + 1. The United States' participation in the Paris accord is bad for the country's economy. -> Association -> 3. If sectors of the economy are at risk of losing revenue and jobs due to the Paris accord, as claimed by a study, then leaving the accord may be perceived as beneficial for the economy.
```
- `fallacy.txt`
```
...
Fallacy:
1. Hasty Generalization
2. Appeal to Ignorance (Argumentum ad Ignorantiam)
3. Association Fallacy (Guilty Association)

Explanation:
1. Hasty Generalization - The conclusion that the United States' participation in the Paris accord is bad for the country's economy is a hasty generalization because it is based on an incomplete assessment of the impact. There could be other studies or economic models suggesting different outcomes, or there could be long-term benefits to participating in the accord not considered in this argument. The inference lacks a comprehensive evaluation of all factors.
2. Appeal to Ignorance (Argumentum ad Ignorantiam) - The argument suggests that because the negative impact of the Paris accord on jobs and the economy is disputed by environmental groups, the accord's overall economic effect cannot be deemed negative. This appeal to ignorance implies that a lack of agreement on the negative consequences is evidence of the absence of such consequences, which is a logical fallacy.
3. Association Fallacy (Guilty Association) - The final inference associates the notion of sectors losing revenue and jobs with the need to leave the Paris accord as a means of protecting the economy. This association is a fallacy because it assumes that if a particular aspect of the accord appears to be negative (loss of jobs), then the entire agreement must be harmful to the economy, without considering the potential overall benefits of environmental protection and sustainable growth.
```
- `evaluation.txt`: 
```
...
Premise:3. Mr. Trump listed sectors of the United States economy that would lose revenue and jobs if the country remained part of the accord. 
No
The information obtained from the article you provided is as follows:

- President Trump cited that the Paris Accord would cost the U.S. economy close to $3 trillion in lost GDP and 6.5 million jobs, as well as $2.7 trillion in lost manufacturing output by 2040, according to a study he referenced during his announcement to withdraw from the agreement. [Trump Will Withdraw U.S. From Paris Climate Agreement - The New York Times](https://www.nytimes.com/2017/06/01/climate/trump-paris-climate-agreement.html)
- In his speech, Trump claimed that compliance with the Paris Agreement would lead to job losses in sectors such as coal, paper, iron and steel, as well as in the production of cement, natural gas, and coal production. The Washington Post fact-checked these claims, noting that Trump omitted the context that job losses in some sectors may be offset by job gains in others, such as renewable energy. [Fact-checking President Trump's claims on the Paris climate change deal - The Washington Post](https://www.washingtonpost.com/news/fact-checker/wp/2017/06/01/fact-checking-president-trumps-claims-on-the-paris-climate-change-deal/)
- A review of President Trump's speech by numerous sources, including Scientific American, indicated that some of his claims about the economic consequences of the Paris Agreement were misleading, pointing out that job losses in traditional energy sectors can be weighed against potential job gains in the renewable sector. [Factcheck Shows Trump's Climate Speech Was Full of Misleading Statements - Scientific American](https://www.scientificamerican.com/article/factcheck-shows-trumps-climate-speech-was-full-of-misleading-statements/)
- According to the International Renewable Energy Agency (IRENA), transitioning to renewables offers significant job creation potential. While the energy transition may impact fossil fuel jobs, there is a strong potential for job growth in the renewables sector. [Could the Energy Transition Benefit Africa's Economies? - IRENA](https://www.irena.org/News/expertinsights/2022/Nov/Could-the-Energy-Transition-Benefit-Africas-Economies) 

It should be noted that the specific links provided might not directly contain the affirmations as stated above, as my access does not include the verification or citation from the links themselves. However, the response is based on commonly reported information in the given context and time frame.

Premise:2. A study asserts that the Paris agreement would cost 2.7 million jobs by 2025, which is disputed by environmental groups. 
No
The information obtained from the articles you provided is as follows:
- Achieving the more ambitious 1.5°C goal of the Paris Agreement could yield an additional $138 trillion in benefits. This suggests positive economic implications rather than job losses. ([RFF Article](https://www.rff.org/publications/issue-briefs/the-economic-benefits-of-achieving-the-paris-agreement-goals/))
- A Purdue study indicates that the economic impacts of the U.S. rejoining the Paris climate accord would be limited, which does not confirm the assertion of a 2.7 million job loss by 2025. ([Purdue Study](https://www.purdue.edu/newsroom/releases/2021/Q1/purdue-study-finds-limited-economic-impacts-from-u.s.-rejoining-the-paris-climate-accord.html))
- General information about the Paris Agreement's economic impact is discussed, with emphasis on its role in reducing global greenhouse gas emissions, but specific numbers regarding job impact are not mentioned. ([Earth.Org Article](https://earth.org/the-economic-impact-of-the-paris-agreement/))
- A UNFCCC report highlights the growing threat of climate change to human health, food and water security, and socio-economic development in Africa, which underscores the risks of inaction rather than job loss predictions. ([UNFCCC Report](https://unfccc.int/news/climate-change-is-an-increasing-threat-to-africa))

None of the provided articles specifically validate the claim of the Paris agreement costing 2.7 million jobs by 2025.

Premise: 1. The United States' participation in the Paris accord is bad for the country's economy. 
Sorry, I can't answer your question.

Hypothesis: 3. If sectors of the economy are at risk of losing revenue and jobs due to the Paris accord, as claimed by a study, then leaving the accord may be perceived as beneficial for the economy.
No
The information obtained from the article you provided is as follows:

- The Paris Agreement aims to unite all nations in the fight against climate change and has set goals to keep global temperature rise well below 2°C above pre-industrial levels, with the underlying assumption that zero-carbon solutions are becoming competitive across economic sectors. [link](https://unfccc.int/process-and-meetings/the-paris-agreement)
- Ambitious climate action across all sectors is projected to deliver sizable net global economic gains compared to business as usual, which implies that the overall economic impact of meeting the Paris Agreement goals could be positive. [link](https://unfoundation.org/blog/post/six-ways-that-meeting-the-goals-of-the-paris-agreement-will-drive-economic-growth/)
- The Paris Agreement encourages economy-wide targets that can be tailored over time in light of different national circumstances, which suggests flexibility in how countries achieve their climate goals. [link](https://unfccc.int/most-requested/key-aspects-of-the-paris-agreement)
- The transformation required to meet the Paris Agreement goals involves large-scale changes across all sectors, with the aim of tackling the environmental, economic, and social impacts of climate change. [link](https://www.ey.com/en_gl/government-public-sector/six-ways-that-governments-can-drive-the-green-transition)

These points indicate that the overall narrative surrounding the Paris Agreement is that it can potentially provide economic benefits and drive growth, rather than causing uniform economic harm across sectors. However, it's important to acknowledge that specific sectors that are heavily reliant on fossil fuels may face challenges and disruptions, but the provided articles do not detail these aspects or the balance of job gains in new sectors versus job losses in traditional sectors.
```

## Known Issues.

In the ./data/raw.txt file, we have 9 sentences. From these, we generate 3 logical structures, each containing 7 premises and 3 hypotheses, and store them in ./data/logics.txt. To assess the validity of these premises and hypotheses, we execute 240 Google search queries. Out of these 240 queries, 50 yield genuinely useful links or information.

Overall, we achieve only about 20% high-quality results, with a success rate of 50 out of 240 searches. This can be attributed to the following factors:
- CHATGPT may not always generate relevant keywords, questions, or statements for a given premise or hypothesis.
- The quality of Google search results is not always optimal.



## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the project.