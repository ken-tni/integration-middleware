import httpx
from typing import Dict, Any, Optional

class CloudERPClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.base_url = config.get("base_url")
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}:{self.api_secret}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    async def get(self, path: str, params: Dict[str, Any] = None):
        response = await self.client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post(self, path: str, data: Dict[str, Any]):
        response = await self.client.post(path, json=data)
        response.raise_for_status()
        return response.json()

    async def put(self, path: str, data: Dict[str, Any]):
        response = await self.client.put(path, json=data)
        response.raise_for_status()
        return response.json()

    async def delete(self, path: str):
        response = await self.client.delete(path)
        response.raise_for_status()
        return response.json() 