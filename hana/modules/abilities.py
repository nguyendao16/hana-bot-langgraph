from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from hana.connection.google_service import GoogleService
from typing import List, Callable
import json
import asyncpg
import asyncio
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

class Abilities:
    def __init__(self, google_service: GoogleService):
        self.google_service = google_service
    
    def get_abilities(self) -> List[Callable]:
        @tool("google_search")
        def google_search(question: str):
            """
            Perform a Google Custom Search using the provided GoogleService instance.
            Args:
                question (str): The search query or question to look up on Google.
            Returns:
                str: JSON string containing filtered search results with important fields only:
                    - search_info: total results and search time
                    - query: the search query
                    - items: list of results with title, link, snippet, and display_link
            """
            raw_result = self.google_service.search(query=question)
            
            filtered = {
                "search_info": {
                    "total_results": raw_result.get("searchInformation", {}).get("totalResults"),
                    "search_time": raw_result.get("searchInformation", {}).get("searchTime"),
                },
                "query": raw_result.get("queries", {}).get("request", [{}])[0].get("searchTerms"),
                "items": []
            }
            
            for item in raw_result.get("items", []):
                filtered_item = {
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                    "display_link": item.get("displayLink")
                }
                filtered["items"].append(filtered_item)
            
            return json.dumps(filtered, ensure_ascii=False, indent=2)
    
        return [google_search]