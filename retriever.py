# Knowledge retriever from provided doc.
import openai
import time
import configparser
import uuid

_MAX_RETRIES = 3

# Create a configparser object
config = configparser.ConfigParser()
# Read the configuration file
config.read('config.ini')

def retrieve(question:str, knowledge:str)->str:
  client = openai.OpenAI(api_key=config['OPENAI']['api_key'])

  # Generate a unique UUID for the filename
  filename = f"data/knowledge/{str(uuid.uuid4())}.txt"

  with open(filename, 'w', encoding='utf-8') as file:
    file.write(knowledge)

  # Upload a file to the assistant".
  file = client.files.create(
    file=open(filename, "rb"),
    purpose='assistants'
  )

  try:
    # Add the file to the assistant
    assistant = client.beta.assistants.create(
      instructions=f"You are a knowledge retrival expert. Use the upload doc to best respond to user's query: {question}",
      model="gpt-4-turbo",
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