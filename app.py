from fastapi import FastAPI
import ollama
import chromadb
import uuid
import os


app = FastAPI()

newpath = './db1' 
if not os.path.exists(newpath):
    os.makedirs(newpath)

ollama_client = ollama.Client(host=os.getenv("OLLAMA_HOST"))

chroma_client = chromadb.PersistentClient(path=newpath)

collection = chroma_client.get_or_create_collection(name="document")


with open("knowledgebase.txt", 'r') as file:
    knowledge_base = file.read()

collection.add(ids=['knowledge_base'], documents=[knowledge_base])

print('Embedding stored in vector db.')

# RAG question from API
@app.post('/query')
def query(q:str):
    base_knowledge = collection.query(
        query_texts=[q],
        n_results=1
    )

    # if the distance between query and base knowledge is close, then 
    # use the base knowledge as context, otherwise pass nothing
    if (base_knowledge['distances'][0][0] > 1):
        context = ""
    else:
        context = base_knowledge['documents'][0][0]

    # get answer from tinyllama model based on context and query
    answer = ollama_client.generate(model='tinyllama', prompt= f"Context: {context} \nQuestion: {q}")

    return {"answer":{answer.response}}

    
# RAG add knowledge
@app.post('/add')
def add_knowledge(text:str):

    try:
        # assign a unique id for the document
        id = uuid.uuid4()

        # add knowledge to chroma's database (local)
        collection.add(ids=[str(id)], documents=[text])

        # add the knowledge to knowledgebase.txt file
        with open("knowledgebase.txt", "a") as file:
            file.write(text + '\n')

        # send back a success message
        return{
            "status":"success",
            "message":"Content added to knowledge base",
            "id": id
        }

    except Exception as e:
        return{
            "status":"error",
            "message":str(e)
        }

