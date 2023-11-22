from http import HTTPStatus
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


async def test_genres_list(es_write_data, make_get_request):
    comedy = {'id': '2a16de1f-9d71-4243-8ca2-242f5054ee20', 'name': 'Comedy'}
    drama = {'id': '6b304ec9-dcf6-49f3-ae16-aa6600923e2d', 'name': 'Drama'}
    await es_write_data('genres', [comedy, drama])

    response = await make_get_request('/api/v1/genres')

    assert response['status'] == HTTPStatus.OK
    assert response['body'] == [
        {'uuid': comedy['id'], 'name': comedy['name']},
        {'uuid': drama['id'], 'name': drama['name']}
    ]


async def test_genres_list_cache(
    es_write_data, make_get_request, redis_client
):
    genre1 = {'id': str(uuid4()), 'name': 'Comedy'}
    await es_write_data('genres', [genre1])
    response = await make_get_request('/api/v1/genres')
    assert len(response['body']) == 1

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    genre2 = {'id': str(uuid4()), 'name': 'Drama'}
    await es_write_data('genres', [genre2])
    response = await make_get_request('/api/v1/genres')
    assert len(response['body']) == 1

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request('/api/v1/genres')
    assert len(response['body']) == 2
