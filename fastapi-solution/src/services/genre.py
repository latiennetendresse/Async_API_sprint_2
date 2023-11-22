from functools import lru_cache
from typing import Optional

from fastapi import Depends

from db.search_engine.base import SearchEngine
from db.search_engine.elastic import get_elastic_search_engine
from models.genre import ESGenre


class GenreService:
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    async def get_by_id(self, genre_id: str) -> Optional[ESGenre]:
        genre = await self.search_engine.get_by_id(
            'genres', genre_id, list(ESGenre.__fields__.keys()))
        return ESGenre(**genre) if genre else None

    async def get_all(self) -> list[ESGenre]:
        genres = await self.search_engine.get_list(
            'genres', fields=list(ESGenre.__fields__.keys()))
        return [ESGenre(**genre) for genre in genres]


@lru_cache()
def get_genre_service(
        search_engine: SearchEngine = Depends(get_elastic_search_engine)
) -> GenreService:
    return GenreService(search_engine)
