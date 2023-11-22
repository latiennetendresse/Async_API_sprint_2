from typing import Any, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import AnyUrl

from db.search_engine.base import SearchEngine


class ElasticSearchEngine(SearchEngine):
    def __init__(self, hosts: list[AnyUrl]):
        self.elastic = AsyncElasticsearch(hosts=hosts)

    async def close(self):
        await self.elastic.close()

    async def get_by_id(self, index: str, id: UUID, fields: list[str]
                        ) -> Any | None:
        try:
            doc = await self.elastic.get(index, id, _source=fields)
        except NotFoundError:
            return None

        return doc['_source']

    async def get_list(
        self, index: str, fields: list[str] = ['*'],
        search_fields: dict[str, str] = {},
        filter_fields: dict[str, list[UUID]] = {},
        sort_params: list[str] = [],
        page_number: int = 1, page_size: int = 1000
    ) -> list[Any]:
        search_from, search_size = ElasticSearchEngine.page_from_size(
            page_number, page_size)
        if not search_size:
            return []

        query = {'bool': {'must': {'match_all': {}}}}
        if search_fields:
            query['bool']['must'] = [
                {
                    'match': {
                        field: {
                            'query': query,
                            'fuzziness': 'auto'
                        }
                    }
                }
                for field, query in search_fields.items()
            ]

        if filter_fields:
            query['bool']['filter'] = {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": field,
                                "query": {
                                    "terms": {
                                        f'{field}.id': ids
                                    }
                                }
                            }
                        }
                        for field, ids in filter_fields.items()
                    ],
                    "minimum_should_match": 1
                }
            }

        docs = await self.elastic.search(
            body={
                "query": query,
                "sort": [ElasticSearchEngine.sort_param_query(param)
                         for param in sort_params],
                "_source": fields,
                "from": search_from,
                "size": search_size,
            },
            index=index
        )
        return [doc['_source'] for doc in docs['hits']['hits']]

    @staticmethod
    def sort_param_query(sort_param: str):
        field = sort_param.strip('-')
        # Text fields are not optimised for sorting. Use a keyword field.
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/multi-fields.html
        if field == 'title':
            field = 'title.raw'

        return {field: 'desc' if sort_param.startswith('-') else 'asc'}

    @staticmethod
    def page_from_size(page_number: int, page_size: int) -> tuple[int, int]:
        """По параметрам страницы возвращает from и size для поиска в Elastic.

        Пагинация с from и size в Elastic даёт просмотреть до 10000 значений:
        https://www.elastic.co/guide/en/elasticsearch/reference/current/paginate-search-results.html
        При необходимости уменьшаем параметры, чтобы вписаться в эти
        ограничения.
        """
        search_from = min((page_number - 1) * page_size, 10000)
        search_size = min(page_size, 10000 - search_from)
        return search_from, search_size


search_engine: Optional[ElasticSearchEngine] = None


async def get_elastic_search_engine() -> ElasticSearchEngine:
    return search_engine
