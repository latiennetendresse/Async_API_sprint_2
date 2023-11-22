import json

import pytest
from elasticsearch import AsyncElasticsearch

from settings import settings
from testdata.es_shemas import ES_SHEMAS


@pytest.fixture(scope='session')
async def es_client():
    client = AsyncElasticsearch(hosts=[settings.elastic_dsn])
    yield client
    await client.close()


@pytest.fixture(autouse=True)
async def es_init(es_client: AsyncElasticsearch):
    """Создаёт индексы для каждого теста и удаляет после завершения."""
    for index in ES_SHEMAS:
        await es_client.indices.create(index, body=ES_SHEMAS[index])

    yield

    for index in ES_SHEMAS:
        await es_client.indices.delete(index)


@pytest.fixture
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(index: str, data: list[dict]):
        bulk_query = []
        for row in data:
            bulk_query.extend([
                json.dumps({'index': {'_index': index, '_id': row['id']}}),
                json.dumps(row)
            ])

        str_query = '\n'.join(bulk_query) + '\n'

        if not await es_client.indices.exists(index):
            raise Exception(
                f'Перед записью данных в индекс {index} его надо '
                f'инициализировать при помощи фикстуры es_{index}_index'
            )
        response = await es_client.bulk(str_query, refresh=True)
        if response['errors']:
            raise Exception('Ошибка записи данных в Elasticsearch')

    return inner
