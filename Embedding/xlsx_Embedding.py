#XLSE ONLY !!!
#XLSE ONLY !!!
#XLSE ONLY !!!
import re
from langchain_community.document_loaders import UnstructuredExcelLoader
import os
from dotenv import load_dotenv
import pandas as ps
load_dotenv()
PG_HOST=os.getenv("PG_HOST")
PG_DBNAME=os.getenv("PG_DBNAME")
PG_USER=os.getenv("PG_USER")
PG_PASSWORD=os.getenv("PG_PASSWORD")
OLLAMA_HOST=os.getenv("OLLAMA_HOST")

print("Input processing...")
excel = ps.read_excel("Tinz.xlsx")
questions = list(excel["question"])
answers = list(excel["answer"])
notes = list(excel["note"])

from langchain_ollama import OllamaEmbeddings
embedding = OllamaEmbeddings(model = "bge-m3:latest",
                              base_url = OLLAMA_HOST) #1024 dim
embedding_list = [] 

print("Embedding...")
for quesion in questions:
    vector = str(embedding.embed_query(quesion))
    embedding_list.append(vector)

import psycopg2
connection = psycopg2.connect(host=PG_HOST, database="AI_DB", user=PG_USER, password=PG_PASSWORD)
cursor = connection.cursor()
print("Storing vectors...")
for i in range(len(embedding_list)):
    question_embedded = embedding_list[i]
    question = questions[i]
    answer = answers[i]
    note = notes[i]
    cursor.execute("INSERT INTO vector_store (question, answer, note, question_embedded) VALUES (%s, %s, %s, %s)", 
                   (question, answer, note, question_embedded))

connection.commit()
cursor.close()
connection.close()

print("Success!")
