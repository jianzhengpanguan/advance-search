import argparse
import logiclinker
import evaluator
import fallacyfinder
import searcher
import json
import retriever

_MAX_ITER = 3

def main():
    parser = argparse.ArgumentParser(description='Process the flags.')
    parser.add_argument('-raw', '--raw_file_path', type=str, default='./data/raw.txt', help='Raw file path')
    parser.add_argument('-ld', '--logics_file_path', type=str, default='./data/logics.txt', help='Logics file path')
    parser.add_argument('-sr', '--search_result_file_path', type=str, default='./data/search_result.txt', help='Search result file path')
    parser.add_argument('-fl', '--fallacy_file_path', type=str, default='./data/fallacy.txt', help='Fallacy file path')
    parser.add_argument('-ev', '--evaluation_file_path', type=str, default='./data/evaluation.txt', help='Evaluation file path')

    args = parser.parse_args()
    print(f"Raw file path: {args.raw_file_path}")
    print(f"Logics file path: {args.logics_file_path}")
    print(f"Fallacy file path: {args.fallacy_file_path}")
    print(f"Evaluation file path: {args.evaluation_file_path}")
    print(f"Search result file path: {args.search_result_file_path}")

    # # Step 1: Convert raw file to logics (i.e., premises, hypothesis and inferences).
    with open(args.raw_file_path, "r", encoding='utf-8') as f:
      raw_statement = f.read()
      logics = logiclinker.fetch_logics(raw_statement)
    
    with open(args.logics_file_path, 'w', encoding='utf-8') as file:
      json.dump(logics, file, indent=2)
    
    # Step 2: Search every premise and hypothesis.
    search_results = []
    retriever.openai_clear()
    with open(args.logics_file_path, "r", encoding='utf-8') as file:
      logics = json.load(file)
      print(f"Number of logics: {len(logics)}")
      for inference in logics:
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
    with open(args.search_result_file_path, 'w') as file:
      json.dump(search_results, file, indent=2, cls=searcher.CustomEncoder)

    # # Step 3: Evaluate each premise and hypothesis.
    retriever.openai_clear()
    with open(args.search_result_file_path, 'r') as search_result_file:
      inference_search_results = json.load(search_result_file)
    with open(args.evaluation_file_path, 'w', encoding='utf-8') as file:
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

    # # Step 4: Find the fallacies.
    with open(args.logics_file_path, "r", encoding='utf-8') as file:
      logics = json.load(file)
    fallacies = fallacyfinder.find(logics)
    with open(args.fallacy_file_path, 'w', encoding='utf-8') as file:
      json.dump(fallacies, file, indent=2, cls=fallacyfinder.CustomEncoder)
      

if __name__ == "__main__":
    main()
