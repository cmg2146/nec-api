"""API Endpoints for Asset Types"""

import os
from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, UploadFile, File, Depends, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app import utils
from app import schemas
from app.database import models
from app.dependencies import get_db
from app.settings import settings
from app.schemas.assets import MAX_ICON_FILE_SIZE_BYTES
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/asset-types",
    tags=["Asset Types"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Create Asset Type
#==========================================================================================
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.AssetType)
async def create_asset_type(
    data: schemas.AssetTypeCreate = Body(description="The new asset type to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new asset type.

    Use the PUT /asset-types/{id}/icon endpoint to upload an icon file after creating
    the asset type.
    """
    asset_type = models.AssetType(**(data.dict()))
    return await crud.create(db, asset_type)

#==========================================================================================
# Query Asset Types
#==========================================================================================
@router.get("/", response_model=list[schemas.AssetType])
async def get_asset_types(
    search: str | None = Query(
        default=None,
        description="Search Field"
    ),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    skip: int | None = Query(
        default=None,
        ge=0,
        description="Skip the specified number of items (for pagination)"
    ),
    limit: int | None = Query(
        default=None,
        ge=1,
        description="Max number of results"
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query asset types"""
    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = select(models.AssetType).order_by(desc(sort_by) if sort_desc else sort_by)
    if search:
        query = query.where(
            models.AssetType.name.icontains(search, autoescape=True) |
            models.AssetType.category.icontains(search, autoescape=True)
        )
    if skip:
        query = query.offset(skip)
    if limit:
        query = query.limit(limit)

    return (await db.scalars(query)).all()

#==========================================================================================
# Get Asset Type
#==========================================================================================
@router.get("/{id}", response_model=schemas.AssetType)
async def get_asset_type(
    id: int = Path(description="The ID of the asset type to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve an asset type by ID."""
    return await crud.get(db, models.AssetType, id)

#==========================================================================================
# Get Asset Type Icon
#==========================================================================================
@router.get("/{id}/icon", response_class=FileResponse)
async def serve_asset_type_icon_file(
    id: int = Path(description="The ID of the asset to get the icon file for"),
    db: AsyncSession = Depends(get_db)
):
    """Serve the actual icon file"""
    asset_type = await crud.get(db, models.AssetType, id)
    if not asset_type.stored_icon_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No icon file uploaded for this asset type"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR, asset_type.stored_icon_filename)

#==========================================================================================
# Upload Asset Type Icon
#==========================================================================================
@router.put("/{id}/icon")
async def upload_asset_type_icon_file(
    id: int = Path(description="The ID of the asset type to upload the icon for"),
    file: UploadFile = File(description="The icon file to upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload/update asset type icon file"""
    asset_type = await crud.get(db, models.AssetType, id)

    utils.validate_file_extension(file, True, ".jpg", ".jpeg", ".png", ".svg")
    new_file_path = await utils.store_uploaded_file(
        file,
        settings.FILE_UPLOAD_DIR,
        MAX_ICON_FILE_SIZE_BYTES
    )
    asset_type.stored_icon_filename = os.path.split(new_file_path)[-1]
    asset_type.original_icon_filename = file.filename

    await crud.update(db, asset_type)

#==========================================================================================
# Update Asset Type
#==========================================================================================
@router.put("/{id}", response_model=schemas.AssetType)
async def update_asset_type(
    id: int = Path(description="The ID of the asset type to update"),
    data: schemas.AssetTypeUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an asset type."""
    asset_type = await crud.get(db, models.AssetType, id)

    dataDict = data.dict(exclude_unset=True)
    for field in dataDict:
        setattr(asset_type, field, dataDict[field])

    return await crud.update(db, asset_type)

#==========================================================================================
# Delete Asset Type
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset_type(
    id: int = Path(description="The ID of the asset type to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an asset type by ID"""
    asset_type = await crud.get(db, models.AssetType, id)

    # Dont allow delete if there are assets of this type
    any_asset = await db.scalar(
        select(models.Asset.id)
        .where(models.Asset.asset_type_id == id)
    )
    if any_asset:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete asset type because there are associated assets"
        )

    await crud.delete(db, asset_type)

#==========================================================================================
# Create Property Name
#==========================================================================================
@router.post(
    "/{id}/property-names",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.AssetPropertyName
)
async def create_property_name(
    id: int = Path(description="The asset type ID"),
    data: schemas.AssetPropertyNameCreate = Body(description="The property name to add"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Add a new property name to the asset type"""
    await crud.raise_if_not_found(db, models.AssetType, id, "Asset Type does not exist")

    dataDict = data.dict()
    dataDict['asset_type_id'] = id
    prop = models.AssetPropertyName(**dataDict)

    return await crud.create(db, prop)

#==========================================================================================
# Get Property Names
#==========================================================================================
@router.get("/{id}/property-names", response_model=list[schemas.AssetPropertyName])
async def get_property_names(
    id: int = Path(description="The asset type ID"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Get asset type's property names"""
    await crud.raise_if_not_found(db, models.AssetType, id, "Asset Type does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.AssetPropertyName)
        .where(models.AssetPropertyName.asset_type_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )

    return (await db.scalars(query)).all()

#==========================================================================================
# Update Property Name
#==========================================================================================
@router.put(
    "/{id}/property-names/{property_name_id}",
    response_model=schemas.AssetPropertyName
)
async def update_property_name(
    id: int = Path(description="The asset type ID"),
    property_name_id: int = Path(description="The ID of the property name to update"),
    data: schemas.AssetPropertyNameUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update asset property name"""
    await crud.raise_if_not_found(db, models.AssetType, id, "Asset Type does not exist")

    #check if prop name exists first
    prop = await db.scalar(
        select(models.AssetPropertyName)
        .where(
            (models.AssetPropertyName.id == property_name_id) &
            (models.AssetPropertyName.asset_type_id == id)
        )
    )
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property name not found"
        )

    dataDict = data.dict(exclude_unset=True)
    for field in dataDict:
        setattr(prop, field, dataDict[field])

    return await crud.update(db, prop)

#==========================================================================================
# Delete Property Name
#==========================================================================================
@router.delete(
    "/{id}/property-names/{property_name_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_property_name(
    id: int = Path(description="The asset type ID"),
    property_name_id: int = Path(description="The ID of the property name to delete"),
    db: AsyncSession = Depends(get_db)
):
    """Delete asset property name"""
    await crud.raise_if_not_found(db, models.AssetType, id, "Asset Type does not exist")

    #check if prop name exists first
    prop = await db.scalar(
        select(models.AssetPropertyName)
        .where(
            (models.AssetPropertyName.id == property_name_id) &
            (models.AssetPropertyName.asset_type_id == id)
        )
    )
    if not prop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property name not found"
        )

    await crud.delete(db, prop)
