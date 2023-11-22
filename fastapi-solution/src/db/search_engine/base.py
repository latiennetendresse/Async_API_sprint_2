from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class SearchEngine(ABC):
    @abstractmethod
    async def get_by_id(self, index: str, id: UUID, fields: list[str]
                        ) -> Any | None:
        pass

    @abstractmethod
    async def get_list(
        self, index: str, fields: list[str],
        search_fields: dict[str, str] = {},
        filter_fields: dict[str, list[UUID]] = {},
        sort_params: list[str] = [],
        page_number: int = 1, page_size: int = 1000
    ) -> list[Any]:
        pass
