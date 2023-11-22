from http import HTTPStatus
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'request_params, expected_response_body',
    [
        (
            {'query': 'Ann'},
            [
                {
                    'uuid': '5fde96c3-ddc6-49fc-816c-efda8304eb20',
                    'full_name': 'Ann',
                    'films': [
                        {
                            'uuid': 'b819ed53-ae49-47fb-b6e0-2cf2b40620e0',
                            'roles': ['actor']
                        },
                        {
                            'uuid': '1879541a-1c5c-40d8-8efd-cbb3f3ad7d0c',
                            'roles': ['actor', 'writer']
                        },
                        {
                            'uuid': '52673667-2427-40d4-a3bd-f81a9ea10f3f',
                            'roles': ['actor', 'writer', 'director']
                        },
                    ]
                }
            ]
        ),
        (
            {'query': 'Bob'},
            [
                {
                    'uuid': '18e16f7c-84b9-4b18-b2a2-dc6d65fc4e5a',
                    'full_name': 'Bob',
                    'films': []
                }
            ]
        ),
    ]
)
async def test_persons_search_format(
    es_write_data, make_get_request,
    request_params, expected_response_body
):
    ann = {'id': '5fde96c3-ddc6-49fc-816c-efda8304eb20', 'name': 'Ann'}
    await es_write_data('persons', [
        {'id': ann['id'], 'full_name': ann['name']},
        {'id': '18e16f7c-84b9-4b18-b2a2-dc6d65fc4e5a', 'full_name': 'Bob'}
    ])
    await es_write_data('movies', [
        {
            'id': 'b819ed53-ae49-47fb-b6e0-2cf2b40620e0',
            'title': 'Movie 1',
            'actors': [ann], 'writers': [], 'directors': [],
        },
        {
            'id': '1879541a-1c5c-40d8-8efd-cbb3f3ad7d0c',
            'title': 'Movie 2',
            'actors': [ann], 'writers': [ann], 'directors': [],
        },
        {
            'id': '52673667-2427-40d4-a3bd-f81a9ea10f3f',
            'title': 'Movie 3',
            'actors': [ann], 'writers': [ann], 'directors': [ann],
        }
    ])

    response = await make_get_request('/api/v1/persons/search', request_params)

    assert response['status'] == HTTPStatus.OK
    assert response['body'] == expected_response_body


@pytest.mark.parametrize(
    'request_params, expected_response_length',
    [
        ({'query': 'Ann', 'page_size': 100}, 60),
        ({'query': 'Bob', 'page_size': 100}, 3),
        ({'query': 'Cat', 'page_size': 100}, 0),
        ({'query': 'Ann Bob', 'page_size': 100}, 63),
        ({'query': 'Ann'}, 50),
        ({'query': 'Ann', 'page_size': 40, 'page_number': 1}, 40),
        ({'query': 'Ann', 'page_size': 40, 'page_number': 2}, 20),
        ({'query': 'Ann', 'page_size': 40, 'page_number': 3}, 0),
    ]
)
async def test_persons_search(
    es_write_data, make_get_request,
    request_params, expected_response_length
):
    data = [
        *[{'id': str(uuid4()), 'full_name': 'Ann'} for _ in range(60)],
        *[{'id': str(uuid4()), 'full_name': 'Bob'} for _ in range(3)],
    ]

    await es_write_data('persons', data)
    response = await make_get_request('/api/v1/persons/search', request_params)

    assert response['status'] == HTTPStatus.OK
    assert len(response['body']) == expected_response_length


@pytest.mark.parametrize(
    'request_params',
    [
        ({'query': 'Ann', 'page_size': 40, 'page_number': -1}),
        ({'query': 'Ann', 'page_size': -1, 'page_number': 1}),
        ({'page_size': 40, 'page_number': 1}),
    ]
)
async def test_persons_search_validation(
    es_write_data, make_get_request, request_params
):
    data = [
        *[{'id': str(uuid4()), 'full_name': 'Ann'} for _ in range(60)],
        *[{'id': str(uuid4()), 'full_name': 'Bob'} for _ in range(3)],
    ]

    await es_write_data('persons', data)
    response = await make_get_request('/api/v1/persons/search', request_params)

    assert response['status'] == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_persons_search_cache(
    es_write_data, make_get_request, redis_client
):
    person1 = {'id': str(uuid4()), 'full_name': 'Ann 1'}
    await es_write_data('persons', [person1])
    response = await make_get_request('/api/v1/persons/search',
                                      {'query': 'Ann'})
    assert len(response['body']) == 1

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    person2 = {'id': str(uuid4()), 'full_name': 'Ann 2'}
    await es_write_data('persons', [person2])
    response = await make_get_request('/api/v1/persons/search',
                                      {'query': 'Ann'})
    assert len(response['body']) == 1

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request('/api/v1/persons/search',
                                      {'query': 'Ann'})
    assert len(response['body']) == 2
