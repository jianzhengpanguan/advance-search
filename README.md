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
3. President Trump listed sectors of the United States economy that would lose revenue and jobs if the United States remained part of the Paris accord. + 2. A study asserts that the Paris agreement would cost the United States economy 2.7 million jobs by 2025, which is disputed by environmental groups. + 1. The United States' participation in the Paris accord is bad for the country's economy. -> Association -> 3. If sectors of the United States economy are at risk of losing revenue and jobs due to the Paris accord, as claimed by a study, then leaving the Paris accord may be perceived as beneficial for the United States economy.

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
Premise:3. President Trump listed sectors of the United States economy that would lose revenue and jobs if the United States remained part of the Paris accord. 
No
The information obtained from the article you provided is as follows:
- [President Trump announced on Thursday that the United States would withdraw from the Paris climate accord, citing that it would lead to lost revenue and jobs in various sectors of the U.S. economy.](https://www.nytimes.com/2017/06/01/climate/trump-paris-climate-agreement.html)
- [In his June 1, 2017 remarks, President Trump made the decision to exit the Paris Agreement based on the belief that it would negatively impact the U.S. economy and workers.](https://2017-2021.state.gov/on-the-u-s-withdrawal-from-the-paris-agreement/)
- [President Trump claimed the Paris Agreement would result in lost jobs, lower wages, shuttered factories, and vastly diminished economic production.](https://trumpwhitehouse.archives.gov/articles/president-trump-announces-u-s-withdrawal-paris-climate-accord/)
- [The Washington Post fact-checked President Trump's claims about the economic repercussions of the Paris Accord, suggesting that many of his statements were misleading.](https://www.washingtonpost.com/news/fact-checker/wp/2017/06/01/fact-checking-president-trumps-claims-on-the-paris-climate-change-deal/)
- [The Guardian analyzed Trump's claims about the Paris climate speech, including the assertion that the Accord would cost the U.S. economy jobs and reduce competitiveness.](https://www.theguardian.com/environment/ng-interactive/2017/jun/02/presidents-paris-climate-speech-annotated-trumps-claims-analysed)
- [The NRDC countered former President Trump's claims regarding the economic harm of the Paris Agreement, pointing to a number of unfounded assertions.](https://www.nrdc.org/stories/paris-climate-agreement-everything-you-need-know)
- A review of President Trump's speech by numerous sources, including Scientific American, indicated that some of his claims about the economic consequences of the Paris Agreement were misleading, pointing out that job losses in traditional energy sectors can be weighed against potential job gains in the renewable sector. [Factcheck Shows Trump's Climate Speech Was Full of Misleading Statements - Scientific American](https://www.scientificamerican.com/article/factcheck-shows-trumps-climate-speech-was-full-of-misleading-statements/)
- According to the International Renewable Energy Agency (IRENA), transitioning to renewables offers significant job creation potential. While the energy transition may impact fossil fuel jobs, there is a strong potential for job growth in the renewables sector. [Could the Energy Transition Benefit Africa's Economies? - IRENA](https://www.irena.org/News/expertinsights/2022/Nov/Could-the-Energy-Transition-Benefit-Africas-Economies) 


Please note that the effectiveness and accuracy of President Trump's arguments have been widely debated and varied opinions exist on the economic implications of the Paris Agreement.

Premise: 2. A study asserts that the Paris agreement would cost the United States economy 2.7 million jobs by 2025, which is disputed by environmental groups. 
No
The information obtained from the article you provided is as follows:
1. The study mentioned with the job loss figures does not appear in the current list of provided links. However, similar claims have been made in the past, often by groups with interests in industries that might be negatively affected by climate policies. (No direct link provided for the specific claim about the 2.7 million job losses)
2. The White House documents and other articles focus on the benefits of adhering to the Paris Agreement and transitioning to a greener economy, including job creation in the renewable energy sector and other economic opportunities. ([The Long-Term Strategy of the United States, Pathways to Net-Zero](https://www.whitehouse.gov/wp-content/uploads/2021/10/us-long-term-strategy.pdf), [FACT SHEET: President Biden Sets 2030 Greenhouse Gas Pollution Reduction Target...](https://www.whitehouse.gov/briefing-room/statements-releases/2021/04/22/fact-sheet-president-biden-sets-2030-greenhouse-gas-pollution-reduction-target-aimed-at-creating-good-paying-union-jobs-and-securing-u-s-leadership-on-clean-energy-technologies/), [FACT SHEET: One Year In, President Biden's Inflation Reduction Act...](https://www.whitehouse.gov/briefing-room/statements-releases/2023/08/16/fact-sheet-one-year-in-president-bidens-inflation-reduction-act-is-driving-historic-climate-action-and-investing-in-america-to-create-good-paying-jobs-and-reduce-costs/))
3. A Purdue study cited finds 'limited economic impacts' from the U.S. rejoining the Paris climate accord, contradicting the claim of extensive job losses. ([Purdue study finds limited economic impacts from U.S. rejoining the Paris climate accord](https://www.purdue.edu/newsroom/releases/2021/Q1/purdue-study-finds-limited-economic-impacts-from-u.s.-rejoining-the-paris-climate-accord.html))

The claim of 2.7 million job losses by 2025 due to the Paris Agreement seems to be an outlier and is not supported by other economic studies and projections included in the links provided. It's also important to note that such projections can be highly dependent on the assumptions and methodologies used in the analyses.

Premise: 1. The United States' participation in the Paris accord is bad for the country's economy. 
No
The information obtained from the article you provided is as follows:
1. A Purdue study suggests limited economic impacts on the U.S. economy from rejoining the Paris climate accord. [Purdue Study](https://www.purdue.edu/newsroom/releases/2021/Q1/purdue-study-finds-limited-economic-impacts-from-u.s.-rejoining-the-paris-climate-accord.html)
2. President Biden's administration argues that tackling climate change by rejoining the Paris Agreement and setting ambitious emissions reduction targets can create good-paying jobs and provide economic opportunities. [White House Fact Sheet 1](https://www.whitehouse.gov/briefing-room/statements-releases/2021/04/22/fact-sheet-president-biden-sets-2030-greenhouse-gas-pollution-reduction-target-aimed-at-creating-good-paying-union-jobs-and-securing-u-s-leadership-on-clean-energy-technologies/)
3. The Inflation Reduction Act promoted by President Biden aims to drive climate action while creating jobs and reducing costs for Americans. [Inflation Reduction Act](https://www.whitehouse.gov/briefing-room/statements-releases/2023/08/16/fact-sheet-one-year-in-president-bidens-inflation-reduction-act-is-driving-historic-climate-action-and-investing-in-america-to-create-good-paying-jobs-and-reduce-costs/)
4. Economic benefits are anticipated from achieving the Paris Agreement goals, with estimates suggesting significant cumulative GDP benefits. [Economic Benefits](https://www.rff.org/publications/issue-briefs/the-economic-benefits-of-achieving-the-paris-agreement-goals/)
5. The White House's long-term strategy outlines benefits such as improvements in public health, climate security, and job growth from adhering to the Paris Agreement targets. [Long-Term Strategy](https://www.whitehouse.gov/wp-content/uploads/2021/10/us-long-term-strategy.pdf)
6. The International Energy Agency (IEA) describes a pathway to net-zero by 2050 that is cost-effective and economically productive. [IEA Report](https://www.iea.org/reports/net-zero-by-2050)

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

In the ./data/raw.txt file, we have 9 sentences. From these, we generate 3 logical structures, containing 7 premises and 3 hypotheses, and store them in ./data/logics.txt. To assess the validity of these premises and hypotheses, we execute 240 Google search queries. Out of these 240 queries, 50 yield genuinely useful links or information.

Overall, we achieve only about 20% high-quality results, with a success rate of 50 out of 240 searches. This can be attributed to the following factors:
- CHATGPT may not always generate relevant keywords, questions, or statements for a given premise or hypothesis.
- The quality of Google search results is not always optimal.



## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the project.