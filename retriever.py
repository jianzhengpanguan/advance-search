# Knowledge retriever from provided doc.
import os
import sys
import openai
import time
import configparser
import uuid
import hashlib
import utils
import signal
import sys
import chromadb
from sentence_transformers import SentenceTransformer
from applog import logger as logging
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

_TOP_K_CHUNKS = 3
_MAX_RETRIES = 3

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

def retrieve(question:str, knowledge:str, provider:utils.ProviderType=utils.ProviderType.unknown)->str:
  # Generate a unique UUID for the filename
  filename = f"data/knowledge/{str(_hash_string_to_uuid(knowledge))}.txt"

  if not os.path.exists(filename):
    with open(filename, 'w', encoding='utf-8') as file:
      file.write(knowledge)

  if provider == utils.ProviderType.openai:
    return openai_retrieve(question, filename)
  return rag_retrieve(question, filename)

def rag_retrieve(question:str, filename:str)->str:

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

def openai_retrieve(question:str, filename:str)->str:
  client = openai.OpenAI(api_key=config['OPENAI']['api_key'])

  # Upload a file to the assistant".
  file = client.files.create(
    file=open(filename, "rb"),
    purpose='assistants'
  )

  try:
    # Add the file to the assistant
    assistant = client.beta.assistants.create(
      instructions=f"You are a knowledge retrival expert. Use the upload doc to best respond to user's query: {question}",
      model=config['OPENAI']['basic_model'], # Use basic model for faster response and save money.
      tools=[{"type": "retrieval"}],
      file_ids=[file.id]
    )
    thread = client.beta.threads.create()
    run = client.beta.threads.runs.create(
      thread_id=thread.id,
      assistant_id=assistant.id
    )
    for _ in range(_MAX_RETRIES):
      retrieved = client.beta.threads.runs.retrieve(
        thread_id=thread.id,
        run_id=run.id
      )
      if retrieved.status == "failed":
        return ""
      if retrieved.status == "completed":
        break
      # Sleep 30 seconds until retrieve run complete.
      time.sleep(30)      
    if retrieved.status != "completed":
      return ""

    thread_messages = client.beta.threads.messages.list(thread.id)
    if not thread_messages.data or not thread_messages.data[-1] or not thread_messages.data[-1].content[-1] or not thread_messages.data[-1].content[-1].text:
      return ""
    logging.info(thread_messages.data[-1].content[-1].text.value)
    return thread_messages.data[-1].content[-1].text.value

  finally:
    # Detaching the file from the assistant removes the file from the retrieval index and means you will no longer be charged for the storage of the indexed file.
    client.beta.assistants.files.delete(
      assistant_id=assistant.id,
      file_id=file.id
    )
    logging.info(f"Deleted file {file.id} from assistant")
    # Delete the assistant because we will be charged for the assitant.
    client.beta.assistants.delete(assistant.id)
    logging.info(f"Deleted assistant {assistant.id}")

def openai_clear():
  client = openai.OpenAI(api_key=config['OPENAI']['api_key'])
  logging.info(f"Clearing OpenAI files: {client.files.list()}")
  for document in client.files.list():
    delete_response = client.files.delete(document.id)
    logging.info(f"Deleted file: {delete_response}")