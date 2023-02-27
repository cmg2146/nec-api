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
    tags=["Floors"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

async def _get(
    id: int,
    db: AsyncSession
) -> models.Floor:
    floor = await db.get(models.Floor, id)
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor not found"
        )

    return floor

async def _raise_404_if_not_found(
    id: int,
    db: AsyncSession
):
    query = select(models.Floor.id).where(models.Floor.id == id)
    floor = await db.scalar(query)
    if not floor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Floor not found"
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
    return await _get(id, db)

@router.put("/{id}", response_model=schemas.Floor)
async def update_floor(
    id: int = Path(description="The ID of the floor to update"),
    data: schemas.FloorUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a floor."""
    floor = await _get(id, db)

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
    floor = await _get(id, db)
    await db.delete(floor)
    await db.commit()


#==========================================================================================
# Overlay Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/overlays/", tags=["Overlays"], status_code=status.HTTP_201_CREATED, response_model=schemas.FloorOverlay)
async def create_overlay(
    id: int = Path(description="The ID of the floor to associate with the overlay"),
    data: schemas.FloorOverlayCreate = Body(description="The new overlay to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new floor overlay"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['floor_id'] = id
    dataDict['extent'] = data.extent.to_wkt()
    dataDict['created'] = datetime.utcnow()

    overlay = models.Floor(**dataDict)
    db.add(overlay)
    await db.commit()
    await db.refresh(overlay)

    return overlay

@router.get("/{id}/overlays/", tags=["Overlays"], response_model=list[schemas.FloorOverlay])
async def get_overlays(
    id: int = Path(description="The ID of the floor to get overlays for"),
    sort_by: schemas.SortBy = Query(default=schemas.SortBy.CREATED, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a floor's overlays"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.FloorOverlay).where(models.FloorOverlay.floor_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()


#==========================================================================================
# Asset Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/assets/", tags=["Assets"], status_code=status.HTTP_201_CREATED, response_model=schemas.Asset)
async def create_asset(
    id: int = Path(description="The ID of the floor to place the asset on"),
    data: schemas.AssetCreate = Body(description="The new asset to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new asset"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['floor_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    asset = models.Asset(**dataDict)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset

@router.get("/{id}/assets/", tags=["Assets"], response_model=list[schemas.Asset])
async def get_assets(
    id: int = Path(description="The ID of the floor to get assets for"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query assets on the specified floor"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Asset).where(models.Asset.floor_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()
