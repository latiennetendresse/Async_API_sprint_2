import logging
from hashlib import md5
from typing import Any, Callable, Optional

from fastapi import Request, Response
from fastapi_cache import Coder, FastAPICache

logger = logging.getLogger(__name__)


def request_key_builder(
    func: Callable,
    namespace: Optional[str] = "",
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
) -> str:
    """Создаёт ключ на основе метода, URL и параметров запроса.

    Функция default_key_builder, используемая по умолчанию, использует kwargs.
    Поэтому разные worker'ы создают разные ключи для одного и того же запроса
    из-за таких параметров, как film_service: FilmService.
    """
    prefix = f'{FastAPICache.get_prefix()}:{namespace}:'
    request_key = ':'.join([
        request.method.upper(),
        request.url.path,
        repr(sorted(request.query_params.items()))
    ])
    return prefix + md5(request_key.encode()).hexdigest()  # noqa: S303


def class_method_key_builder(
    func: Callable,
    namespace: Optional[str] = "",
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
) -> str:
    """Создаёт ключ на основе метода класса и параметров запроса.

    Аргумент self не учитывается, чтобы разные worker'ы не создавали разные
    ключи для одного и того же запроса.
    """
    prefix = f'{FastAPICache.get_prefix()}:{namespace}:'
    call_key = f'{func.__module__}:{func.__name__}:{args[1:]}:{kwargs}'
    logger.info(f'Call key: {call_key}')
    return prefix + md5(call_key.encode()).hexdigest()  # noqa: S303


def get_model_coder(model):
    class ModelCoder(Coder):
        @classmethod
        def encode(cls, value: Any) -> bytes:
            return model.json(value)

        @classmethod
        def decode(cls, value: bytes) -> Any:
            return model.parse_raw(value)

    return ModelCoder
