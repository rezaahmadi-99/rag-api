import chromadb
import os


newpath = './db1' 
if not os.path.exists(newpath):
    os.makedirs(newpath)

chroma_client = chromadb.PersistentClient(path=newpath)

collection = chroma_client.get_or_create_collection(name="document")


with open("k8s.txt", 'r') as file:
    k8s_content = file.read()

collection.add(ids=['k8s'], documents=[k8s_content])

print('Embedding stored in vector db.')


