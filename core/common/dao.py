from typing import Generic, TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from core.common.exceptions import DuplicateResourceError

TableModel = TypeVar("TableModel", bound=SQLModel)
CreateModel = TypeVar("CreateModel")
UpdateModel = TypeVar("UpdateModel")


class BaseDAO(Generic[TableModel, CreateModel, UpdateModel]):
    def __init__(self, session: AsyncSession, model: type[TableModel]) -> None:
        self._session = session
        self._model = model

    async def create(self, data: CreateModel) -> TableModel:
        if isinstance(data, SQLModel):
            payload = data.model_dump()
        elif hasattr(data, "model_dump"):
            payload = data.model_dump()
        else:
            payload = dict(data)

        instance = self._model.model_validate(payload)
        self._session.add(instance)
        try:
            await self._session.commit()
            await self._session.refresh(instance)
        except IntegrityError as exc:
            await self._session.rollback()
            raise DuplicateResourceError() from exc
        return instance
