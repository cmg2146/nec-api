"""API Endpoints for Assets"""

from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Asset Resource Operations
#==========================================================================================
@router.get("/", response_model=list[schemas.Asset])
async def get_assets(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query assets"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Asset).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.Asset)
async def get_asset(
    id: int = Path(description="The ID of the asset to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve an asset by ID."""
    result = await db.get(models.Asset, id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    return result

@router.put("/{id}", response_model=schemas.Asset)
async def update_asset(
    id: int = Path(description="The ID of the asset to update"),
    data: schemas.AssetUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an asset."""
    asset = await db.get(models.Asset, id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    dataDict = data.dict(exclude_unset=True)
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(asset, field, dataDict[field])

    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    id: int = Path(description="The ID of the asset to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an asset by ID"""
    asset = await db.get(models.Asset, id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found"
        )

    await db.delete(asset)
    await db.commit()


#==========================================================================================
# Property Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/properties", status_code=status.HTTP_201_CREATED, response_model=schemas.AssetProperty)
async def create_property(
    id: int = Path(description="The asset ID"),
    data: schemas.AssetPropertyCreate = Body(description="The property to add"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Add a new property to the asset"""
    dataDict = data.dict()
    dataDict['created'] = datetime.utcnow()

    prop = models.AssetProperty(**dataDict)
    db.add(prop)
    await db.commit()
    await db.refresh(prop)

    return prop

@router.get("/{id}/properties", response_model=list[schemas.AssetProperty])
async def get_properties(
    id: int = Path(description="The asset ID"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Get asset's properties"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.AssetProperty).where(models.AssetProperty.asset_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()

@router.put("/{id}/properties/{property_id}", response_model=schemas.AssetProperty)
async def update_property(
    id: int = Path(description="The asset ID"),
    property_id: int = Path(description="The ID of the property to update"),
    data: schemas.AssetPropertyUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an asset property"""
    #check if prop exists first
    query = select(models.AssetProperty).where(
        models.AssetProperty.id == property_id &
        models.AssetProperty.asset_id == id
    )
    prop = await db.scalar(query)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    dataDict = data.dict(exclude_unset=True)
    dataDict['modified'] = datetime.utcnow()
    for field in dataDict:
        setattr(prop, field, dataDict[field])

    db.add(prop)
    await db.commit()
    await db.refresh(prop)

    return prop
