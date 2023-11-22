import logging
from functools import lru_cache
from typing import Optional
from uuid import UUID

from fastapi import Depends

from db.search_engine.base import SearchEngine
from db.search_engine.elastic import get_elastic_search_engine
from models.film import ESFilm
from models.person import ROLES, ESPerson, ESPersonFilm

logger = logging.getLogger(__name__)


class PersonService:
    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    async def get_by_id(self, person_id: UUID) -> Optional[ESPerson]:
        person = await self.search_engine.get_by_id(
            'persons', person_id, fields=['id', 'full_name'])

        if not person:
            return None

        films = await self.search_engine.get_list(
            'movies', fields=['id', 'actors', 'writers', 'directors'],
            search_fields={},
            filter_fields={f'{role}s': [person_id] for role in ROLES}
        )
        return ESPerson(films=self._get_person_films(person_id, films),
                        **person)

    async def search(self, query: str, page_number: int, page_size: int
                     ) -> list[ESPerson]:
        persons = await self.search_engine.get_list(
            'persons', fields=['id', 'full_name'],
            search_fields={'full_name': query},
            filter_fields={}, sort_params=[],
            page_number=page_number, page_size=page_size
        )

        person_ids = [person['id'] for person in persons]
        films = await self.search_engine.get_list(
            'movies', fields=['id', 'actors', 'writers', 'directors'],
            search_fields={},
            filter_fields={f'{role}s': person_ids for role in ROLES}
        )

        return [
            ESPerson(films=self._get_person_films(person['id'], films),
                     **person)
            for person in persons
        ]

    async def list_films(self, person_id: UUID) -> list[ESFilm]:
        films = await self.search_engine.get_list(
            'movies', fields=['id', 'title', 'imdb_rating'],
            search_fields={},
            filter_fields={f'{role}s': [person_id] for role in ROLES}
        )

        return [ESFilm(**film) for film in films]

    def _get_person_films(self, person_id: UUID, films: list
                          ) -> list[ESPersonFilm]:
        return [
            ESPersonFilm(id=film['id'], roles=roles)
            for film in films
            if (roles := self._get_person_roles(person_id, film))
        ]

    def _get_person_roles(self, person_id: UUID, film) -> list[str]:
        return [
            role for role in ROLES
            if str(person_id) in self._get_film_role_person_ids(film, role)
        ]

    def _get_film_role_person_ids(self, film, role: str) -> list[UUID]:
        return [p['id'] for p in film.get(f'{role}s', [])]


@lru_cache()
def get_person_service(
    search_engine: SearchEngine = Depends(get_elastic_search_engine)
) -> PersonService:
    return PersonService(search_engine)
