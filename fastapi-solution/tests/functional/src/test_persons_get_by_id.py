from http import HTTPStatus

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    'person_id, expected_response',
    [
        (
            '5fde96c3-ddc6-49fc-816c-efda8304eb20',
            {
                'status': HTTPStatus.OK,
                'body': {
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
            }
        ),
        (
            '18e16f7c-84b9-4b18-b2a2-dc6d65fc4e5a',
            {
                'status': HTTPStatus.OK,
                'body': {
                    'uuid': '18e16f7c-84b9-4b18-b2a2-dc6d65fc4e5a',
                    'full_name': 'Bob',
                    'films': []
                }
            }
        ),
        (
            '8d02d3e6-ec26-4ec8-80dd-8cf43e429e15',
            {
                'status': HTTPStatus.NOT_FOUND,
                'body': {'detail': 'person not found'}
            }
        ),
    ]
)
async def test_persons_get_by_id(
    es_write_data, make_get_request,
    person_id, expected_response
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

    response = await make_get_request(f'/api/v1/persons/{person_id}')

    assert response['status'] == expected_response['status']
    assert response['body'] == expected_response['body']


async def test_persons_get_by_id_cache(
    es_write_data, make_get_request, redis_client
):
    person_id = '5fde96c3-ddc6-49fc-816c-efda8304eb20'

    await es_write_data('persons', [{'id': person_id, 'full_name': 'Ann'}])
    response = await make_get_request(f'/api/v1/persons/{person_id}')
    assert response['body']['full_name'] == 'Ann'

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    await es_write_data('persons', [{'id': person_id, 'full_name': 'Bob'}])
    response = await make_get_request(f'/api/v1/persons/{person_id}')
    assert response['body']['full_name'] == 'Ann'

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request(f'/api/v1/persons/{person_id}')
    assert response['body']['full_name'] == 'Bob'
