import logging.config

import httpx
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis.asyncio import Redis

from api.v1 import films, genres, persons
from core.logging import LOGGING
from core.settings import settings
from db import redis
from db.search_engine import elastic
from utils import http
from utils.cache import request_key_builder

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='movies',
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)


@app.on_event('startup')
async def startup():
    redis.redis = Redis.from_url(settings.redis_dsn)
    FastAPICache.init(RedisBackend(redis.redis),
                      prefix='fastapi-cache',
                      key_builder=request_key_builder)
    elastic.search_engine = elastic.ElasticSearchEngine(
        hosts=[settings.elastic_dsn])
    http.client = httpx.AsyncClient()


@app.on_event('shutdown')
async def shutdown():
    await redis.redis.close()
    await elastic.search_engine.close()
    await http.client.aclose()


app.include_router(films.router, prefix='/api/v1/films', tags=['Фильмы'])
app.include_router(persons.router, prefix='/api/v1/persons', tags=['Персоны'])
app.include_router(genres.router, prefix='/api/v1/genres', tags=['Жанры'])
