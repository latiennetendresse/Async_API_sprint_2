from typing import Optional

from pydantic import AnyUrl, BaseSettings, RedisDsn


class Settings(BaseSettings):
    auth_url: Optional[AnyUrl] = None
    elastic_dsn: AnyUrl = 'http://127.0.0.1:9200'
    redis_dsn: RedisDsn = 'redis://127.0.0.1:6379'
    redis_cache_expire_seconds: int = 300
    log_level: str = 'INFO'


settings = Settings()
