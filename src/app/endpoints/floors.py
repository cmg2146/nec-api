"""API Endpoints for Floors"""

from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/floors",
    tags=["floors"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Floor Resource Operations
#==========================================================================================
@router.get("/", response_model=list[schemas.Floor])
async def get_floors(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query floors"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Floor).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.Floor)
async def get_floor(
    id: int = Path(description="The ID of the floor to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a floor by ID."""
    floor = await db.get(models.Floor, id)
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor not found"
        )

    return floor

@router.put("/{id}", response_model=schemas.Floor)
async def update_floor(
    id: int = Path(description="The ID of the floor to update"),
    data: schemas.FloorUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a floor."""
    floor = await db.get(models.Floor, id)
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor not found"
        )

    dataDict = data.dict(exclude_unset=True)
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(floor, field, dataDict[field])

    db.add(floor)
    await db.commit()
    await db.refresh(floor)

    return floor

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_floor(
    id: int = Path(description="The ID of the floor to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a floor by ID"""
    floor = await db.get(models.Floor, id)
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor not found"
        )

    await db.delete(floor)
    await db.commit()


#==========================================================================================
# Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/overlays/", tags=["overlays"], status_code=status.HTTP_201_CREATED, response_model=schemas.FloorOverlay)
async def create_overlay(
    id: int = Path(description="The ID of the floor to associated with the overlay"),
    data: schemas.FloorOverlayCreate = Body(description="The new overlay to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new floor overlay"""
    dataDict = data.dict()
    dataDict['floor_id'] = id
    dataDict['extent'] = data.extent.to_wkt()
    dataDict['created'] = datetime.utcnow()

    overlay = models.Floor(**dataDict)
    db.add(overlay)
    await db.commit()
    await db.refresh(overlay)

    return overlay

@router.get("/{id}/overlays/", tags=["overlays"], response_model=list[schemas.FloorOverlay])
async def get_overlays(
    id: int = Path(description="The ID of the floor to get overlays for"),
    sort_by: schemas.SortBy = Query(default=schemas.SortBy.CREATED, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a floor's overlays"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.FloorOverlay).where(models.FloorOverlay.floor_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()
