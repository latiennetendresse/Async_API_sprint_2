from http import HTTPStatus
from uuid import uuid4

import pytest

pytestmark = pytest.mark.asyncio

MOVIE1_ID = 'b819ed53-ae49-47fb-b6e0-2cf2b40620e0'
MOVIE2_ID = '1879541a-1c5c-40d8-8efd-cbb3f3ad7d0c'
ANN_ID = '5fde96c3-ddc6-49fc-816c-efda8304eb20'
BOB_ID = '18e16f7c-84b9-4b18-b2a2-dc6d65fc4e5a'
CAT_ID = '382ed8d1-30aa-4b34-9484-17c6a505ece2'
COMEDY_ID = '5373d043-3f41-4ea8-9947-4b746c601bbd'
DRAMA_ID = '1cacff68-643e-4ddd-8f57-84b62538081a'


@pytest.mark.parametrize(
    'film_id, expected_response',
    [
        (
            MOVIE1_ID,
            {
                'status': HTTPStatus.OK,
                'body': {
                    'uuid': MOVIE1_ID, 'title': 'Film 1',
                    'imdb_rating': 1.1, 'description': 'Text 1',
                    'genre': [
                        {'uuid': COMEDY_ID, 'name': 'Comedy'},
                        {'uuid': DRAMA_ID, 'name': 'Drama'},
                    ],
                    'actors': [
                        {'uuid': ANN_ID, 'full_name': 'Ann'},
                        {'uuid': BOB_ID, 'full_name': 'Bob'},
                    ],
                    'writers': [
                        {'uuid': ANN_ID, 'full_name': 'Ann'},
                        {'uuid': CAT_ID, 'full_name': 'Cat'},
                    ],
                    'directors': [
                        {'uuid': BOB_ID, 'full_name': 'Bob'},
                        {'uuid': CAT_ID, 'full_name': 'Cat'},
                    ]
                }
            }
        ),
        (
            MOVIE2_ID,
            {
                'status': HTTPStatus.OK,
                'body': {
                    'uuid': MOVIE2_ID, 'title': 'Film 2',
                    'imdb_rating': 2.2, 'description': '',
                    'genre': [], 'actors': [], 'writers': [], 'directors': []
                }
            }
        ),
        (
            'e28b3360-3275-4022-ac18-df5c83397946',
            {
                'status': HTTPStatus.NOT_FOUND,
                'body': {'detail': 'film not found'}
            }
        ),
        (
            'invalid_id',
            {
                'status': HTTPStatus.UNPROCESSABLE_ENTITY,
                'body': {
                    'detail': [{'loc': ['path', 'film_id'],
                                'msg': 'value is not a valid uuid',
                                'type': 'type_error.uuid'}]
                }
            }
        ),
    ]
)
async def test_films_get_by_id(
    es_write_data, make_get_request,
    film_id, expected_response
):
    ann = {'id': ANN_ID, 'name': 'Ann'}
    bob = {'id': BOB_ID, 'name': 'Bob'}
    cat = {'id': CAT_ID, 'name': 'Cat'}
    await es_write_data('movies', [
        {
            'id': MOVIE1_ID, 'title': 'Film 1',
            'imdb_rating': 1.1, 'description': 'Text 1',
            'genres': [
                {'id': COMEDY_ID, 'name': 'Comedy'},
                {'id': DRAMA_ID, 'name': 'Drama'}
            ],
            'actors': [ann, bob],
            'writers': [ann, cat],
            'directors': [bob, cat],
        },
        {
            'id': MOVIE2_ID, 'title': 'Film 2',
            'imdb_rating': 2.2, 'description': '',
            'genres': [], 'actors': [], 'writers': [], 'directors': [],
        },
    ])

    response = await make_get_request(f'/api/v1/films/{film_id}')

    assert response['status'] == expected_response['status']
    assert response['body'] == expected_response['body']


async def test_films_get_by_id_cache(
    es_write_data, make_get_request, redis_client
):
    film = {
        'id': str(uuid4()), 'title': 'The Matrix 1',
        'imdb_rating': 8.7,  'description': 'Text',
        'genres': [], 'actors': [], 'writers': [], 'directors': []
    }
    await es_write_data('movies', [film])
    response = await make_get_request(f'/api/v1/films/{film["id"]}')
    assert response['body']['title'] == 'The Matrix 1'

    # Запрос возвращает данные из кэша, несмотря на обновление в ES.
    film['title'] = 'The Matrix 2'
    await es_write_data('movies', [film])
    response = await make_get_request(f'/api/v1/films/{film["id"]}')
    assert response['body']['title'] == 'The Matrix 1'

    # После сброса кэша запрос возврашает свежие данные из ES.
    await redis_client.flushall()
    response = await make_get_request(f'/api/v1/films/{film["id"]}')
    assert response['body']['title'] == 'The Matrix 2'
