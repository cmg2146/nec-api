"""API Endpoints for Asset Types"""

import os
from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db
from app.settings import settings

router = APIRouter(
    prefix="/asset-types",
    tags=["Asset Types"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

async def _get(
    id: int,
    db: AsyncSession
) -> models.AssetType:
    asset_type = await db.get(models.AssetType, id)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset Type not found"
        )

    return asset_type

async def _raise_404_if_not_found(
    id: int,
    db: AsyncSession
):
    query = select(models.AssetType.id).where(models.AssetType.id == id)
    asset_type = await db.scalar(query)
    if not asset_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset Type not found"
        )

#==========================================================================================
# Asset Type Resource Operations
#==========================================================================================
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.AssetType)
async def create_asset_type(
    data: schemas.AssetTypeCreate = Body(description="The new asset type to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new asset type"""
    dataDict = data.dict()
    dataDict['created'] = datetime.utcnow()

    asset_type = models.AssetType(**dataDict)
    db.add(asset_type)
    await db.commit()
    await db.refresh(asset_type)

    return asset_type

@router.get("/", response_model=list[schemas.AssetType])
async def get_asset_types(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query asset types"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.AssetType).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.AssetType)
async def get_asset_type(
    id: int = Path(description="The ID of the asset type to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve an asset type by ID."""
    return await _get(id, db)

@router.get("/{id}/icon", response_class=FileResponse)
async def serve_asset_type_icon_file(
    id: int = Path(description="The ID of the asset to get the icon file for"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Serve the actual icon file"""
    asset_type = await _get(id, db)

    if not asset_type.stored_icon_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No icon file uploaded for this asset type"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR.absolute, asset_type.stored_icon_filename)

@router.put("/{id}", response_model=schemas.AssetType)
async def update_asset_type(
    id: int = Path(description="The ID of the asset type to update"),
    data: schemas.AssetTypeUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an asset type."""
    asset_type = await _get(id, db)

    dataDict = data.dict(exclude_unset=True)
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(asset_type, field, dataDict[field])

    db.add(asset_type)
    await db.commit()
    await db.refresh(asset_type)

    return asset_type

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_type(
    id: int = Path(description="The ID of the asset type to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an asset type by ID"""
    asset_type = await _get(id, db)

    # Dont allow delete if there are assets of this type
    query = select(models.Asset.id).where(models.Asset.asset_type_id == id)
    asset = await db.scalar(query)
    if asset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete asset type because there are associated assets"
        )

    await db.delete(asset_type)
    await db.commit()


#==========================================================================================
# Property Name Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/property-names", status_code=status.HTTP_201_CREATED, response_model=schemas.AssetPropertyName)
async def create_property_name(
    id: int = Path(description="The asset type ID"),
    data: schemas.AssetPropertyNameCreate = Body(description="The property name to add"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Add a new property name to the asset type"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['asset_type_id'] = id
    dataDict['created'] = datetime.utcnow()

    prop = models.AssetPropertyName(**dataDict)
    db.add(prop)
    await db.commit()
    await db.refresh(prop)

    return prop

@router.get("/{id}/property-names", response_model=list[schemas.AssetPropertyName])
async def get_property_names(
    id: int = Path(description="The asset type ID"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Get asset type's property names"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.AssetPropertyName).where(models.AssetPropertyName.asset_type_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()

@router.put("/{id}/property-names/{property_name_id}", response_model=schemas.AssetPropertyName)
async def update_property_name(
    id: int = Path(description="The asset type ID"),
    property_name_id: int = Path(description="The ID of the property name to update"),
    data: schemas.AssetPropertyNameUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update asset property name"""
    await _raise_404_if_not_found(id, db)

    #check if prop name exists first
    query = select(models.AssetPropertyName).where(
        models.AssetPropertyName.id == property_name_id &
        models.AssetPropertyName.asset_type_id == id
    )
    prop = await db.scalar(query)
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property name not found"
        )

    dataDict = data.dict(exclude_unset=True)
    dataDict['modified'] = datetime.utcnow()
    for field in dataDict:
        setattr(prop, field, dataDict[field])

    db.add(prop)
    await db.commit()
    await db.refresh(prop)

    return prop
