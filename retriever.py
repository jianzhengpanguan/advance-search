# Knowledge retriever from provided doc.
import os
import sys
import openai
import time
import configparser
import uuid
import gpt
import hashlib
import utils
import signal
import sys
import chromadb
from applog import logger as logging
from sentence_transformers import SentenceTransformer
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

_TOP_K_CHUNKS = 3
_RETRIVE_PROMPT_TOKENS = 50

embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')

# Create a Chroma client
chroma_client = chromadb.Client()

def __init__():
  # Start the Chroma server
  chroma_client.start_server()
  # Function to handle shutdown signals
  def _shutdown_handler(signum, _):
    logging.info(f"Shutdown signal {signum} received. Shutting down the server.")
    chroma_client.stop_server()
    sys.exit(0)
  # Setup signal handlers for graceful shutdown
  signal.signal(signal.SIGINT, _shutdown_handler)
  signal.signal(signal.SIGTERM, _shutdown_handler)

def _embedding_function(doc:str):
  return embedding_model.encode([doc])[0].tolist()

def _hash_string_to_uuid(input_string):
  # Create a SHA-1 hash object
  hasher = hashlib.sha1()
  # Update the hash object with the input string, encoded to bytes
  hasher.update(input_string.encode('utf-8'))
  # Get the SHA-1 hash of the string
  hash_bytes = hasher.digest()
  # Create a UUID based on the first 16 bytes of the SHA-1 hash
  return uuid.UUID(bytes=hash_bytes[:16])

def _knowledge_to_file(question:str, knowledge:str) -> str:
  if not knowledge:
    logging.warning(f"Knowledge is empty: question: {question}, knowledge: {knowledge}")
    return ""

  # Generate a unique UUID for the filename
  filename = f"data/knowledge/{str(_hash_string_to_uuid(knowledge))}.txt"

  if not os.path.exists(filename):
    with open(filename, 'w', encoding='utf-8') as file:
      file.write(knowledge)
  
  return filename

def local_retrieve(question:str, knowledge:str)->str:
  print(utils.num_tokens_from_messages(question + knowledge))
  if utils.num_tokens_from_messages(question + knowledge) + _RETRIVE_PROMPT_TOKENS < int(config['LLAMA']['context_window']):
    try:
      prompt = f"""
      You are a knowledge retrival expert.
      Use the upload doc: {knowledge} 
      Try to respond to user's query: {question}
      """
      return gpt.llama_request(prompt, utils.ModelType.basic_model)
    except Exception as e:
      logging.warning(f"Failed to retrieve knowledge using OpenAI with the context window: {e}")
  return rag_retrieve(question, knowledge)

def rag_retrieve(question:str, knowledge:str)->str:
  filename = _knowledge_to_file(knowledge)
  # Use the uuid from the filename.
  unique_id = filename.split("/")[-1].replace(".txt", "")
  # Create or reuse a existing collection
  try:
    collection = chroma_client.get_collection(unique_id)
  except Exception as e:
    collection = chroma_client.create_collection(name=unique_id)
    # load the document and split it into chunks
    loader = TextLoader(filename, encoding='utf-8')
    documents = loader.load()

    # split by seperators, then merge them to slightly more than chunk size.
    text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", "\r", "\t"], chunk_size=500, chunk_overlap=25)
    docs = [doc.page_content for doc in text_splitter.split_documents(documents)]

    # Add all docs.
    for id, doc in enumerate(docs):
      collection.add(
        documents=[doc], 
        ids=[f"file{unique_id}id{id}"],
        embeddings=[_embedding_function(doc)]
      )

  # Perform a similarity search
  find_docs = collection.query(
      query_embeddings=[_embedding_function(question)],
      n_results=_TOP_K_CHUNKS,
      include=["documents"]
  )

  logging.info(f"filename: {filename}, docs size: {len(str(find_docs))}")
  return "\n".join([doc for doc in find_docs["documents"][0]])

def openai_retrieve(question:str, knowledge:str, model_type:utils.ModelType=utils.ModelType.basic_model)->str:
  if utils.num_tokens_from_messages(question + knowledge) + _RETRIVE_PROMPT_TOKENS < int(config['OPENAI']['context_window']):
    try:
      prompt = f"""
      You are a knowledge retrival expert.
      Use the upload doc: {knowledge} 
      Try to respond to user's query: {question}
      """
      return gpt.openai_request(prompt, utils.ModelType.basic_model)
    except Exception as e:
      logging.warning(f"Failed to retrieve knowledge using OpenAI with the context window: {e}")

  filename = _knowledge_to_file(knowledge)
  client = openai.OpenAI(api_key=config['OPENAI']['api_key'])

  # Upload a file to the assistant".
  file = client.files.create(
    file=open(filename, "rb"),
    purpose='assistants'
  )

  # By default, use basic model for faster response and save money.
  model = config['OPENAI']['basic_model']
  if model_type == utils.ModelType.advance_model:
    model = config['OPENAI']['advance_model']

  assistant = None
  try:
    # Add the file to the assistant
    assistant = client.beta.assistants.create(
      instructions="You are a knowledge retrival expert.",
      model=model, 
      tools=[{"type": "file_search"}],
    )
    thread = client.beta.threads.create(
      messages=[
        {
          "role": "user",
          "content": f"Use the upload doc to best respond to user's query: {question}",
          # Attach the new file to the message.
          "attachments": [
            { "file_id": file.id, "tools": [{"type": "file_search"}] }
          ],
        }
      ]
    )
    # Create and poll ensure we received a response from the assistant.
    # Either failure or completion.
    run = client.beta.threads.runs.create_and_poll(
      thread_id=thread.id,
      assistant_id=assistant.id
    )
    thread_messages = client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id)
    if not thread_messages.data or not thread_messages.data[-1] or not thread_messages.data[-1].content[-1] or not thread_messages.data[-1].content[-1].text:
      logging.error(f"The retrieving returns no data, openai_retrieve({question} {filename})")
      return ""
    logging.info(thread_messages.data[-1].content[-1].text.value)
    return thread_messages.data[-1].content[-1].text.value

  except Exception as e:
    logging.error(f"Error when retrieving, openai_retrieve({question} {filename}): {e}")
    return ""

  finally:
    # If no assistant defined, skip.
    if assistant == None:
      return
    # Removes the file.
    client.files.delete(file.id)
    logging.info(f"Deleted file {file.id}")
    # Delete the assistant.
    client.beta.assistants.delete(assistant.id)
    logging.info(f"Deleted assistant {assistant.id}")

def openai_clear():
  client = openai.OpenAI(api_key=config['OPENAI']['api_key'])
  docs = client.files.list()
  if not docs:
    return
  logging.info(f"Clearing OpenAI files: {docs}")
  for document in docs:
    delete_response = client.files.delete(document.id)
    logging.info(f"Deleted file: {delete_response}")
