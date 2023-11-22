from pydantic import AnyUrl, BaseSettings, RedisDsn


class TestSettings(BaseSettings):
    elastic_dsn: AnyUrl = 'http://127.0.0.1:9200'
    redis_dsn: RedisDsn = 'redis://127.0.0.1:6379'
    api_url: AnyUrl = 'http://127.0.0.1:8000'


settings = TestSettings()
