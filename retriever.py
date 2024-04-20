# Knowledge retriever from provided doc.
import openai
import time
import configparser
import uuid
import utils
import signal
import sys
import chromadb
from langchain_community.document_loaders import TextLoader
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter


_TOP_K_CHUNKS = 3
_MAX_RETRIES = 3

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config/config.ini')

def __init__():
  # Create a Chroma client
  chroma_client = chromadb.Client()
  # Start the Chroma server
  chroma_client.start_server()
  # Function to handle shutdown signals
  def _shutdown_handler(signum, _):
    print(f"Shutdown signal {signum} received. Shutting down the server.")
    chroma_client.stop_server()
    sys.exit(0)
  # Setup signal handlers for graceful shutdown
  signal.signal(signal.SIGINT, _shutdown_handler)
  signal.signal(signal.SIGTERM, _shutdown_handler)

def retrieve(question:str, knowledge:str, provider:utils.ProviderType=utils.ProviderType.unknown)->str:
  # Generate a unique UUID for the filename
  filename = f"data/knowledge/{str(uuid.uuid4())}.txt"

  with open(filename, 'w', encoding='utf-8') as file:
    file.write(knowledge)

  if provider == utils.ProviderType.openai:
    return openai_retrieve(question, filename)
  return rag_retrieve(question, filename)

def rag_retrieve(question:str, filename:str)->str:
  # load the document and split it into chunks
  loader = TextLoader(filename, encoding='utf-8')
  documents = loader.load()

  # split by seperators, then merge them to slightly more than chunk size.
  text_splitter = RecursiveCharacterTextSplitter(separators=["\n\n", "\n", "\r", "\t"], chunk_size=500, chunk_overlap=25)
  docs = text_splitter.split_documents(documents)
  # create the open-source embedding function
  embedding_function = SentenceTransformerEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

  # load it into Chroma
  db = Chroma.from_documents(docs, embedding_function)
  
  # find the most similar document to our question.
  find_docs = db.similarity_search(question, k=_TOP_K_CHUNKS)
  results = []
  for doc in find_docs:
    if doc.metadata and doc.metadata["source"] == filename:
      results.append(doc.page_content)
  print(f"filename: {filename}, docs size: {len(str(results))}")
  return "\n".join(results)

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
      model=config['OPENAI']['basic_model'],
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
      # Sleep 10 seconds until retrieve run complete.
      time.sleep(10)
      
    if retrieved.status != "completed":
      return ""

    thread_messages = client.beta.threads.messages.list(thread.id)
    return thread_messages.data[-1].content

  finally:
    # Detaching the file from the assistant removes the file from the retrieval index and means you will no longer be charged for the storage of the indexed file.
    client.beta.assistants.files.delete(
      assistant_id=assistant.id,
      file_id=file.id
    )
    print(f"Deleted file {file.id} from assistant")
    # Delete the assistant because we will be charged for the assitant.
    client.beta.assistants.delete(assistant.id)
    print(f"Deleted assistant {assistant.id}")