import argparse
import logiclinker
import evaluator
import fallacyfinder
import fallacysolver
import searcher
import json
import retriever
import utils
from applog import logger as logging

_MAX_ITER = 3

def main():
    parser = argparse.ArgumentParser(description='Process the flags.')
    parser.add_argument('-folder', '--folder_path', type=str, default='./data/7. Peter Thiel send J.D. Vance to Trump', help='Folder path')
    args = parser.parse_args()
    raw_file_path = f'{args.folder_path}/raw.txt'
    logics_file_path = f'{args.folder_path}/logics.txt'

    # Step 1: Convert raw file to logics (i.e., premises, hypothesis and inferences).
    with open(raw_file_path, "r", encoding='utf-8') as f:
      raw_statement = f.read()
      logics = logiclinker.fetch_logics(raw_statement, provider=utils.ProviderType.anthropic, model=utils.ModelType.advance_model)
    
    with open(logics_file_path, 'w', encoding='utf-8') as file:
      json.dump(logics, file, indent=2)
    

if __name__ == "__main__":
    main()
