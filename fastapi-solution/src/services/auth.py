import logging
from functools import lru_cache

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from core.settings import settings
from utils.http import get_http_client

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, http_client: httpx.AsyncClient):
        self.http_client = http_client

    async def check_access(
        self, creds: HTTPAuthorizationCredentials,
        allow_roles: list[str] = None
    ) -> None:
        if not settings.auth_url:
            return

        if not creds:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Not authenticated')

        try:
            response = await self.http_client.get(
                f'{settings.auth_url}/api/v1/check_access',
                params={'allow_roles': allow_roles},
                headers={
                    'Authorization': f'{creds.scheme} {creds.credentials}'
                }
            )
            if response.status_code != status.HTTP_204_NO_CONTENT:
                raise HTTPException(status_code=response.status_code,
                                    detail=response.json().get('detail', ''))
        except httpx.HTTPError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Auth service unavailable')


@lru_cache()
def get_auth_service(
    http_client: httpx.AsyncClient = Depends(get_http_client)
) -> AuthService:
    return AuthService(http_client)
