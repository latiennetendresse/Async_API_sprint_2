import logging
from functools import lru_cache
from typing import Literal, Optional
from uuid import UUID

from fastapi import Depends
from fastapi_cache.decorator import cache

from core.settings import settings
from db.search_engine.base import SearchEngine
from db.search_engine.elastic import get_elastic_search_engine
from models.film import ESFilm, ESFilmFull, ESFilmPerson
from models.genre import ESGenre
from models.person import ROLES
from utils.cache import class_method_key_builder, get_model_coder

logger = logging.getLogger(__name__)


class FilmService:
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    @cache(expire=settings.redis_cache_expire_seconds,
           key_builder=class_method_key_builder,
           coder=get_model_coder(ESFilmFull))
    async def get_by_id(self, film_id: UUID) -> Optional[ESFilmFull]:
        film = await self.search_engine.get_by_id(
            'movies', film_id, fields=list(ESFilmFull.__fields__.keys()))

        if not film:
            return None

        flat_fields = ['id', 'title', 'imdb_rating', 'description']
        nested_fields = {
            'genres': ESGenre,
            **{f'{role}s': ESFilmPerson for role in ROLES}
        }
        return ESFilmFull(
            **{field: film[field] for field in flat_fields},
            **{
                field: [model(**item) for item in film[field]]
                for field, model in nested_fields.items()
            },
        )

    async def search(self, query: str, page_number: int, page_size: int
                     ) -> list[ESFilm]:
        films = await self.search_engine.get_list(
            'movies', fields=list(ESFilm.__fields__.keys()),
            search_fields={'title': query},
            filter_fields={}, sort_params=[],
            page_number=page_number, page_size=page_size
        )
        return [ESFilm(**film) for film in films]

    async def list(self,
                   genre_id: Optional[UUID],
                   sort_params: list[Literal[
                       'imdb_rating', '-imdb_rating',
                       'title', '-title']
                   ],
                   page_number: int, page_size: int) -> list[ESFilm]:
        filter_fields = {}
        if genre_id:
            filter_fields['genres'] = [str(genre_id)]

        films = await self.search_engine.get_list(
            'movies', fields=list(ESFilm.__fields__.keys()),
            search_fields={},
            filter_fields=filter_fields,
            sort_params=sort_params,
            page_number=page_number, page_size=page_size
        )
        return [ESFilm(**film) for film in films]


@lru_cache()
def get_film_service(
    search_engine: SearchEngine = Depends(get_elastic_search_engine)
) -> FilmService:
    return FilmService(search_engine)
