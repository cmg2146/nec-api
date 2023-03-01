from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseDbModel

TModelType = TypeVar("TModelType", BaseDbModel)

async def get(
    db: AsyncSession,
    model_type: Type[TModelType],
    id: int,
    raise_if_not_found: bool = True
) -> TModelType:
    """Gets an item with the specified type and id from the database.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model_type: BaseDbModel
            The entity type to retrieve. Must be instance of BaseDbModel.
        id: int
            The id of the record to get.
        raise_if_not_found: bool
            Indicates if a 404 HTTPException should be raised if the item
            is not found.
    """
    result = await db.get(model_type, id)

    if raise_if_not_found and not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return result

async def raise_if_not_found(
    db: AsyncSession,
    model_type: Type[TModelType],
    id: int,
    not_found_message: str = "Item does not exist"
):
    """Raises an HTTPException if the item with the specified type and id is not found.

    This method is more efficient than a full get because it only queries the
    id column.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model_type: BaseDbModel
            The entity type to retrieve. Must be instance of BaseDbModel.
        id: int
            The id of the record to check.
        not_found_message: str
            Used as the exception detail if item is not found.
    """
    query = select(model_type.id).where(model_type.id == id)
    result = await db.scalar(query)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_message
        )
