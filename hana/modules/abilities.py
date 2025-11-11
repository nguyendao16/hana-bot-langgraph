from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
import asyncpg
import json
from os import getenv
from dotenv import load_dotenv

load_dotenv()
PG_VECTORDB = getenv("PG_VECTORDB")
PG_HOST = getenv("PG_HOST")
PG_DBNAME = getenv("PG_DBNAME")
PG_USER = getenv("PG_USER")
PG_PASSWORD = getenv("PG_PASSWORD")
OLLAMA_HOST = getenv("OLLAMA_HOST")
OLLAMAEMBEDDING_MODEL = getenv("OLLAMAEMBEDDING_MODEL")

embeddings = OllamaEmbeddings(model = OLLAMAEMBEDDING_MODEL,
                              base_url = OLLAMA_HOST)

@tool("rag_search")
async def rag_search(question, user):
    """
    Args:
        text (str): The input question or query to be searched.
    Returns:
        str: JSON string containing the generated answer based on retrieved relevant information with rank of similarity.
    """
    conn_vectorstore = await asyncpg.connect(host=PG_HOST, database=PG_VECTORDB, user=PG_USER, password=PG_PASSWORD)
    vector = str(embeddings.embed_query(question))

    # đổi placeholder từ %s thành $1
    rows = await conn_vectorstore.fetch(
        """SELECT question, answer, (question_embedded <=> $1::vector) AS cosine_similarity FROM vector_store
                        ORDER BY cosine_similarity
                        LIMIT 3""", vector
    )
    await conn_vectorstore.close()

    results = []
    for row in rows:
        result = {}
        result["question"] = row[0]
        result["answer"] = row[1]
        result["note"] = row[2]
        results.append(result)
    
    return json.dumps(results, ensure_ascii=False, indent=0)
