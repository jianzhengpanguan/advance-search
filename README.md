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
- `evaluation.txt`: Provides an evaluation summary of the opinions and facts.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the project.