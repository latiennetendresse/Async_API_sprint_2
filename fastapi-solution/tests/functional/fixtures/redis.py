import pytest
from redis.asyncio import Redis

from settings import settings


@pytest.fixture(scope='session')
async def redis_client():
    client = Redis.from_url(settings.redis_dsn)
    yield client
    await client.close()


@pytest.fixture(autouse=True)
async def redis_flushall(redis_client):
    """Сбрасывает кэш в Redis для каждого теста."""
    await redis_client.flushall()
