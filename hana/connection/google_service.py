from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GoogleService:
    def __init__(self, api_key: str, cx: str):
        self.api_key = api_key
        self.cx = cx
        self.service = None
    
    def build_google_service(self):
        if self.service is not None:
            return self.service
        try:
            print("Building GoogleService...")
            self.service = build("customsearch", "v1", developerKey=self.api_key)
        except HttpError as e:
            print(f"[GoogleService] Failed to build service: {e}")
            raise
        except Exception as e:
            print(f"[GoogleService] Unexpected error: {e}")
            raise
        return self.service

    def search(self, query: str) -> dict:
        service = self.service or self.build_google_service()
        try:
            res = (
                service.cse()
                .list(q=query, cx=self.cx)
                .execute()
            )
            return res
        except HttpError as e:
            print(f"[GoogleService] HTTP error during search: {e}")
            raise
