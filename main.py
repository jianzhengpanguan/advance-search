import argparse
import logiclinker
import evaluator
import fallacyfinder
import fallacysolver
import searcher
import json
import retriever
import utils
import os
from applog import logger as logging

_MAX_ITER = 3

def main():
    parser = argparse.ArgumentParser(description='Process the flags.')
    parser.add_argument('-folder', '--folder_path', type=str, default='./data/7. Peter Thiel send J.D. Vance to Trump', help='Folder path')
    args = parser.parse_args()
    raw_file_path = f'{args.folder_path}/raw.txt'
    all_logics_file_path = f'{args.folder_path}/logics.txt'

    # Step 1: Split logics.
    with open(all_logics_file_path, 'r', encoding='utf-8') as file:
      logics = json.load(file)

    for i, logic in enumerate(logics):
      folder_path = f'{args.folder_path}/{i}'
      logics_file_path = f'{folder_path}/logics.txt'
      search_result_file_path = f'{folder_path}/search_result.txt'
      evaluation_file_path = f'{folder_path}/evaluation.txt'
      fallacy_file_path = f'{folder_path}/fallacy.txt'
      fallacy_search_result_file_path = f'{folder_path}/fallacy_search_result.txt'
      fallacy_evaluation_file_path = f'{folder_path}/fallacy_evaluation.txt'
      
      print(f"Raw file path: {raw_file_path}")
      print(f"Logics file path: {logics_file_path}")
      print(f"Evaluation file path: {evaluation_file_path}")
      print(f"Search result file path: {search_result_file_path}")
      print(f"Fallacy file path: {fallacy_file_path}")
      print(f"Fallacy search result file path: {fallacy_search_result_file_path}")
      print(f"Fallacy evaluation file path: {fallacy_evaluation_file_path}")

      # Step 1: Save logic to subfolder.
      os.makedirs(folder_path, exist_ok=True)
      with open(logics_file_path, 'w', encoding='utf-8') as file:
        json.dump(logic, file, indent=2)

      # Step 2: Search every premise and hypothesis.
      search_results = []
      retriever.openai_clear()
      with open(logics_file_path, "r", encoding='utf-8') as file:
        inference = json.load(file)
      # Parse inference.
      inference_search_result = {"premises": [], "hypothesis": []}
      for premise in inference["premises"]:
        if premise == '':
          continue
        inference_search_result["premises"].append({premise:searcher.search(premise, _MAX_ITER)})
      for hypothesis in inference["hypothesis"]:
        if hypothesis == '':
          continue
        inference_search_result["hypothesis"].append({hypothesis:searcher.search(hypothesis, _MAX_ITER)})
      search_results.append(inference_search_result)
      retriever.openai_clear()
      with open(search_result_file_path, 'w') as file:
        json.dump(search_results, file, indent=2, cls=searcher.CustomEncoder)

      # Step 3: Evaluate each premise and hypothesis.
      retriever.openai_clear()
      with open(search_result_file_path, 'r') as search_result_file:
        inference_search_results = json.load(search_result_file)
      with open(evaluation_file_path, 'w', encoding='utf-8') as file:
        for inference_search_result in inference_search_results:
          for premise_search_results in inference_search_result["premises"]:
            premise_search_results:dict[str, searcher.SearchResults]
            for premise, search_results in premise_search_results.items():
              if premise == '':
                continue
              file.write('Premise:' + premise + '\n')
              file.write(evaluator.evaluate(premise, str(search_results)) + '\n\n')
          for hypothesis_search_results in inference_search_result["hypothesis"]:
            hypothesis_search_results:list[dict[str, dict[str, list[str]]]]
            for hypothesis, search_results in hypothesis_search_results.items():
              if hypothesis == '':
                continue
              file.write('Hypothesis:' + hypothesis + '\n')
              file.write(evaluator.evaluate(hypothesis, str(search_results)) + '\n\n')
      retriever.openai_clear()

      # Step 4: Find the fallacies.
      retriever.openai_clear()
      with open(logics_file_path, "r", encoding='utf-8') as file:
        logic = json.load(file)
      fallacies = fallacyfinder.find([logic])
      with open(fallacy_file_path, 'w', encoding='utf-8') as file:
        json.dump(fallacies, file, indent=2)
      retriever.openai_clear()

      # Step 5: Search more to avoid/solve the fallacies.
      retriever.openai_clear()
      with open(fallacy_file_path, "r", encoding='utf-8') as file:
        fallacies = json.load(file)
      fallacy_search_results = fallacysolver.solve(fallacies)
      with open(fallacy_search_result_file_path, 'w', encoding='utf-8') as file:
        json.dump(fallacy_search_results, file, indent=2, cls=fallacysolver.CustomEncoder)
      retriever.openai_clear()

      # Step 6: Evaluate the new premise and hypothesis.
      retriever.openai_clear()
      with open(fallacy_search_result_file_path, 'r') as search_result_file:
        inference_fallacy_search_results = json.load(search_result_file)
      with open(fallacy_evaluation_file_path, 'w', encoding='utf-8') as file:
        for inference, fallacy_search_results in inference_fallacy_search_results.items():
          file.write('Inference:' + inference + '\n')
          for fallacy_search_result in fallacy_search_results:
            if "search" not in fallacy_search_result or "search_results" not in fallacy_search_result:
              logging.info(f"search or search_results not exists in {fallacy_search_result}")
              continue
            search = fallacy_search_result["search"]
            search_results = fallacy_search_result["search_results"]
            if not search or not search_results:
              logging.info(f"search or search_results is empty in {fallacy_search_result}")
              continue
            file.write('Premise/Hypothesis:' + search + '\n')
            file.write(evaluator.evaluate(search, str(search_results)) + '\n\n')
      retriever.openai_clear()


if __name__ == "__main__":
    main()
