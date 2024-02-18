import argparse
import logiclinker
import evaluator


def main():
    parser = argparse.ArgumentParser(description='Process the flags.')
    parser.add_argument('-raw', '--raw_file_path', type=str, default='./data/raw.txt', help='Raw file path')
    parser.add_argument('-ld', '--logics_file_path', type=str, default='./data/logics.txt', help='Logics file path')
    parser.add_argument('-ev', '--evaluation_file_path', type=str, default='./data/evaluation.txt', help='Evaluation file path')

    args = parser.parse_args()
    print(f"Raw file path: {args.raw_file_path}")
    print(f"Logics file path: {args.logics_file_path}")
    print(f"Evaluation file path: {args.evaluation_file_path}")

    # # Step 1: Convert raw file to logics (i.e., premises, hypothesis and inferences).
    # with open(args.raw_file_path, "r", encoding='utf-8') as f:
    #   raw_statement = f.read()
    #   logics = logiclinker.fetch_logics(raw_statement)
    
    # with open(args.logics_file_path, 'w', encoding='utf-8') as file:
    #   for logic in logics:
    #     file.write(logic + '\n')
    
    # Step 2: Evaluate the logics.
    with open(args.logics_file_path, "r", encoding='utf-8') as f:
      logics = f.readlines()
      print(f"Number of logics: {len(logics)}")
      with open(args.evaluation_file_path, 'w', encoding='utf-8') as file:
        for logic in logics:
          statements = logic.split('->')
          if len(statements) != 3:
            continue
          for premise in statements[0].split('+'):
            if premise == '':
              continue
            file.write('Premise:' + premise + '\n')
            file.write(evaluator.evaluate(premise) + '\n\n')
          for hypothesis in statements[2].split('+'):
            if hypothesis == '':
              continue
            file.write('Hypothesis:' + hypothesis + '\n')
            file.write(evaluator.evaluate(hypothesis) + '\n\n')
          

if __name__ == "__main__":
    main()
