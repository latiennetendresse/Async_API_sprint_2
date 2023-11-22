from http import HTTPStatus

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'genre_id, expected_response',
    [
        (
            '5373d043-3f41-4ea8-9947-4b746c601bbd',
            {
                'status': HTTPStatus.OK,
                'body': {
                    'uuid': '5373d043-3f41-4ea8-9947-4b746c601bbd',
                    'name': 'Comedy'
                }
            }
        ),
        (
            '1cacff68-643e-4ddd-8f57-84b62538081a',
            {
                'status': HTTPStatus.OK,
                'body': {
                    'uuid': '1cacff68-643e-4ddd-8f57-84b62538081a',
                    'name': 'Drama'
                }
            }
        ),
        (
            'b92ef010-5e4c-4fd0-99d6-41b6456272cd',
            {
                'status': HTTPStatus.NOT_FOUND,
                'body': {'detail': 'genre not found'}
            }
        ),
    ]
)
async def test_genres_get_by_id(
    es_write_data, make_get_request,
    genre_id, expected_response
):
    data = [
        {
            'id': '5373d043-3f41-4ea8-9947-4b746c601bbd',
            'name': 'Comedy'
        },
        {
            'id': '1cacff68-643e-4ddd-8f57-84b62538081a',
            'name': 'Drama'
        },
    ]

    await es_write_data('genres', data)
    response = await make_get_request(f'/api/v1/genres/{genre_id}')

    assert response['status'] == expected_response['status']
    assert response['body'] == expected_response['body']


async def test_genres_get_by_id_cache(
    es_write_data, make_get_request, redis_client
):
    genre_id = '5373d043-3f41-4ea8-9947-4b746c601bbd'

    await es_write_data('genres', [{'id': genre_id, 'name': 'Comedy'}])
    response = await make_get_request(f'/api/v1/genres/{genre_id}')
    assert response['body']['name'] == 'Comedy'

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    await es_write_data('genres', [{'id': genre_id, 'name': 'Drama'}])
    response = await make_get_request(f'/api/v1/genres/{genre_id}')
    assert response['body']['name'] == 'Comedy'

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request(f'/api/v1/genres/{genre_id}')
    assert response['body']['name'] == 'Drama'
