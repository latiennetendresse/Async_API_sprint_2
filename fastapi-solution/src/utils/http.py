from typing import Optional

import httpx

client: Optional[httpx.AsyncClient] = None


async def get_http_client() -> httpx.AsyncClient:
    return client
