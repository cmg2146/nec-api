"""CRUD helpers for API endpoints"""

from datetime import datetime
from typing import Type, TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import BaseDbModel

TModelType = TypeVar("TModelType", bound=BaseDbModel)

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
        model_type: Type[BaseDbModel]
            The entity type to retrieve. Must be type of BaseDbModel.
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

async def get_all_with_limit(
    db: AsyncSession,
    model_type: Type[TModelType],
    skip: int,
    limit: int,
    sort_by: str,
    sort_desc: bool = False
):
    """Retrieves records of a specified type without a predicate.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model_type: Type[BaseDbModel]
            The entity type to retrieve records for. Must be type of BaseDbModel.
        skip: int
            OFFSET applied to the result set.
        limit: int
            Max number of results to return.
        sort_by: str
            Name of column to sort by.
        sort_desc: bool = False
            Use descending sort direction, default False.
    """
    query = (
        select(model_type)
        .order_by(desc(sort_by) if sort_desc else sort_by)
        .offset(skip)
        .limit(limit)
    )
    return (await db.scalars(query)).all()

async def create(
    db: AsyncSession,
    model: TModelType
):
    """Creates or Updates a record in the database.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model: BaseDbModel
            The entity to update. Must be instance of BaseDbModel.
    """
    model.created = datetime.utcnow()

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return model

async def update(
    db: AsyncSession,
    model: TModelType
):
    """Updates a record in the database.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model: BaseDbModel
            The entity to update. Must be instance of BaseDbModel.
    """
    model.modified = datetime.utcnow()

    db.add(model)
    await db.commit()
    await db.refresh(model)

    return model

async def delete(
    db: AsyncSession,
    model_type: Type[TModelType],
    id: int,
):
    """Deletes a record from the database with the specified type and id.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model_type: Type[BaseDbModel]
            The entity type to retrieve. Must be type of BaseDbModel.
        id: int
            The id of the record to check.
    """
    item = await get(db, model_type, id)

    await db.delete(item)
    await db.commit()

async def delete(
    db: AsyncSession,
    model: TModelType
):
    """Deletes a record from the database.

    Parameters:
        db: AsyncSession
            The SQLAlchemy database session.
        model: BaseDbModel
            The entity to update. Must be instance of BaseDbModel.
    """
    await db.delete(model)
    await db.commit()

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
        model_type: Type[BaseDbModel]
            The entity type to retrieve. Must be type of BaseDbModel.
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
