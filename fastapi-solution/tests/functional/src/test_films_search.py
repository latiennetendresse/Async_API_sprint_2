from http import HTTPStatus
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'request_params, expected_response_length',
    [
        ({'query': 'Godfather', 'page_size': 100}, 60),
        ({'query': 'Matrix', 'page_size': 100}, 3),
        ({'query': 'Star Wars', 'page_size': 100}, 0),
        ({'query': 'Godfather Matrix', 'page_size': 100}, 63),
        ({'query': 'Godfather'}, 50),
        ({'query': 'Godfather', 'page_size': 40, 'page_number': 1}, 40),
        ({'query': 'Godfather', 'page_size': 40, 'page_number': 2}, 20),
        ({'query': 'Godfather', 'page_size': 40, 'page_number': 3}, 0),
    ]
)
async def test_films_search(
    es_write_data, make_get_request,
    request_params, expected_response_length
):
    data = [
        *[
            {'id': str(uuid4()), 'title': 'The Godfather', 'imdb_rating': 9.2}
            for _ in range(60)
        ],
        *[
            {'id': str(uuid4()), 'title': 'The Matrix', 'imdb_rating': 8.7}
            for _ in range(3)
        ],
    ]

    await es_write_data('movies', data)
    response = await make_get_request('/api/v1/films/search', request_params)

    assert response['status'] == HTTPStatus.OK
    assert len(response['body']) == expected_response_length
    assert all([set(item.keys()) == {'uuid', 'title', 'imdb_rating'}
                for item in response['body']])


@pytest.mark.parametrize(
    'request_params',
    [
        ({'query': 'Godfather', 'page_size': 40, 'page_number': -1}),
        ({'query': 'Godfather', 'page_size': -1, 'page_number': 1}),
        ({'page_size': 40, 'page_number': 1}),
    ]
)
async def test_films_search_validation(
    es_write_data, make_get_request, request_params
):
    data = [
        *[
            {'id': str(uuid4()), 'title': 'The Godfather', 'imdb_rating': 9.2}
            for _ in range(60)
        ],
        *[
            {'id': str(uuid4()), 'title': 'The Matrix', 'imdb_rating': 8.7}
            for _ in range(3)
        ],
    ]

    await es_write_data('movies', data)
    response = await make_get_request('/api/v1/films/search', request_params)

    assert response['status'] == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_films_search_cache(
    es_write_data, make_get_request, redis_client
):
    film1 = {'id': str(uuid4()), 'title': 'The Matrix 1', 'imdb_rating': 8.7}
    await es_write_data('movies', [film1])
    response = await make_get_request('/api/v1/films/search',
                                      {'query': 'Matrix'})
    assert len(response['body']) == 1

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    film2 = {'id': str(uuid4()), 'title': 'The Matrix 2', 'imdb_rating': 7.2}
    await es_write_data('movies', [film2])
    response = await make_get_request('/api/v1/films/search',
                                      {'query': 'Matrix'})
    assert len(response['body']) == 1

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request('/api/v1/films/search',
                                      {'query': 'Matrix'})
    assert len(response['body']) == 2
