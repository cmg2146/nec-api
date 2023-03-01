"""API Endpoints for Assets"""

from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/assets",
    tags=["Assets"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Query Assets
#==========================================================================================
@router.get("/", response_model=list[schemas.Asset])
async def get_assets(
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    skip: int = Query(
        default=0,
        description="Skip the specified number of items (for pagination)"
    ),
    limit: int = Query(
        default=100,
        description="Max number of results"
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query assets"""
    return await crud.get_all_with_limit(
        db,
        models.Asset,
        skip,
        limit,
        sort_by,
        sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    )

#==========================================================================================
# Get Asset
#==========================================================================================
@router.get("/{id}", response_model=schemas.Asset)
async def get_asset(
    id: int = Path(description="The ID of the asset to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve an asset by ID."""
    return await crud.get(db, models.Asset, id)

#==========================================================================================
# Update Asset
#==========================================================================================
@router.put("/{id}", response_model=schemas.Asset)
async def update_asset(
    id: int = Path(description="The ID of the asset to update"),
    data: schemas.AssetUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an asset."""
    asset = await crud.get(db, models.Asset, id)

    dataDict = data.dict(exclude_unset=True)
    dataDict['coordinates'] = data.coordinates.to_wkt()
    for field in dataDict:
        setattr(asset, field, dataDict[field])

    return await crud.update(db, asset)

#==========================================================================================
# Delete Asset
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    id: int = Path(description="The ID of the asset to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an asset by ID"""
    await crud.delete(db, models.Asset, id)

#==========================================================================================
# Create Asset Property
#==========================================================================================
@router.post(
    "/{id}/properties",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.AssetProperty
)
async def create_property(
    id: int = Path(description="The asset ID"),
    data: schemas.AssetPropertyCreate = Body(description="The property to add"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Add a new property to the asset"""
    await crud.raise_if_not_found(db, models.Asset, id, "Asset does not exist")

    dataDict = data.dict()
    dataDict['asset_id'] = id
    prop = models.AssetProperty(**dataDict)

    return await crud.create(db, prop)

#==========================================================================================
# Get Asset's Properties
#==========================================================================================
@router.get("/{id}/properties", response_model=list[schemas.AssetProperty])
async def get_properties(
    id: int = Path(description="The asset ID"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Get asset's properties"""
    await crud.raise_if_not_found(db, models.Asset, id, "Asset does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.AssetProperty)
        .where(models.AssetProperty.asset_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )

    return (await db.scalars(query)).all()

#==========================================================================================
# Update Asset Property
#==========================================================================================
@router.put("/{id}/properties/{property_id}", response_model=schemas.AssetProperty)
async def update_property(
    id: int = Path(description="The asset ID"),
    property_id: int = Path(description="The ID of the property to update"),
    data: schemas.AssetPropertyUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an asset property"""
    await crud.raise_if_not_found(db, models.Asset, id, "Asset does not exist")

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
    for field in dataDict:
        setattr(prop, field, dataDict[field])

    return await crud.update(db, prop)

#==========================================================================================
# Update Asset Property
#==========================================================================================
@router.delete("/{id}/properties/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_property(
    id: int = Path(description="Asset ID"),
    property_id: int = Path("ID of the asset property to delete"),
    db: AsyncSession = Depends(get_db)
):
    await crud.raise_if_not_found(db, models.Asset, id, "Asset does not exist")

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

    await crud.delete(db, prop)
