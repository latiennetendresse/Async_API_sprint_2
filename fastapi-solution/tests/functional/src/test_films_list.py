from http import HTTPStatus
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'request_params, expected_list',
    [
        ({'sort': ['imdb_rating']}, [1, 2, 0]),
        ({'sort': ['-imdb_rating']}, [0, 2, 1]),
        ({'sort': ['title']}, [2, 0, 1]),
        ({'sort': ['-title']}, [1, 0, 2]),
        (
            {'genre': '2a16de1f-9d71-4243-8ca2-242f5054ee20',
             'sort': ['imdb_rating']},
            [2, 0]
        ),
        (
            {'genre': '2a16de1f-9d71-4243-8ca2-242f5054ee20',
             'sort': ['-imdb_rating']},
            [0, 2]
        ),
    ]
)
async def test_films_list(
    es_write_data, make_get_request,
    request_params, expected_list
):
    comedy = {'id': '2a16de1f-9d71-4243-8ca2-242f5054ee20', 'name': 'Comedy'}
    drama = {'id': '6b304ec9-dcf6-49f3-ae16-aa6600923e2d', 'name': 'Drama'}
    data = [
        {
            'title': 'Movie 2', 'imdb_rating': 3.0,
            'genres': [comedy], 'id': str(uuid4())
        },
        {
            'title': 'Movie 3', 'imdb_rating': 1.0,
            'genres': [drama], 'id': str(uuid4())
        },
        {
            'title': 'Movie 1', 'imdb_rating': 2.0,
            'genres': [comedy, drama], 'id': str(uuid4())
        },
    ]
    await es_write_data('movies', data)

    response = await make_get_request('/api/v1/films', request_params)

    assert response['status'] == HTTPStatus.OK
    assert [
        [film[field] for field in ('uuid', 'title', 'imdb_rating')]
        for film in response['body']
    ] == [
        [data[i][field] for field in ('id', 'title', 'imdb_rating')]
        for i in expected_list
    ]


@pytest.mark.parametrize(
    'request_params, expected_response_length',
    [
        ({'page_size': 100}, 60),
        ({}, 50),
        ({'page_size': 40, 'page_number': 1}, 40),
        ({'page_size': 40, 'page_number': 2}, 20),
        ({'page_size': 40, 'page_number': 3}, 0),
    ]
)
async def test_films_list_pagination(
    es_write_data, make_get_request,
    request_params, expected_response_length
):
    data = [
        {'id': str(uuid4()), 'title': 'The Godfather', 'imdb_rating': 9.2}
        for _ in range(60)
    ]

    await es_write_data('movies', data)
    response = await make_get_request('/api/v1/films', request_params)

    assert response['status'] == HTTPStatus.OK
    assert len(response['body']) == expected_response_length


@pytest.mark.parametrize(
    'request_params',
    [
        ({'sort': ['invalid_sort_param']}),
        ({'genre': 'invalid_id'}),
        ({'page_size': 40, 'page_number': -1}),
        ({'page_size': -1, 'page_number': 1}),
    ]
)
async def test_films_list_validation(
    es_write_data, make_get_request, request_params
):
    data = [
        {'id': str(uuid4()), 'title': 'The Godfather', 'imdb_rating': 9.2}
        for _ in range(60)
    ]

    await es_write_data('movies', data)
    response = await make_get_request('/api/v1/films', request_params)

    assert response['status'] == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_films_list_cache(
    es_write_data, make_get_request, redis_client
):
    film1 = {'id': str(uuid4()), 'title': 'The Matrix 1', 'imdb_rating': 8.7}
    await es_write_data('movies', [film1])
    response = await make_get_request('/api/v1/films')
    assert len(response['body']) == 1

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    film2 = {'id': str(uuid4()), 'title': 'The Matrix 2', 'imdb_rating': 7.2}
    await es_write_data('movies', [film2])
    response = await make_get_request('/api/v1/films')
    assert len(response['body']) == 1

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request('/api/v1/films')
    assert len(response['body']) == 2
