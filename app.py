from fastapi import FastAPI
import ollama
import chromadb
import uuid
from embedding import newpath 
import os


app = FastAPI()

newpath = './db1' 
if not os.path.exists(newpath):
    os.makedirs(newpath)

chroma_client = chromadb.PersistentClient(path=newpath)

collection = chroma_client.get_or_create_collection(name="document")


with open("k8s.txt", 'r') as file:
    k8s_content = file.read()

collection.add(ids=['k8s'], documents=[k8s_content])

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
    answer = ollama.generate(model='tinyllama', prompt= f"Context: {context} \nQuestion: {q}")

    return {"answer":{answer.response}}

    
# RAG add knowledge
@app.post('/add')
def add_knowledge(text:str):

    try:
        # assign a unique id for the document
        id = uuid.uuid4()

        # add knowledge to chroma's database (local)
        collection.add(ids=[str(id)], documents=[text])

        # add the knowledge to k8s.txt file
        with open("k8s.txt", "a") as file:
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

