"""API Endpoints for Floors"""

import os
from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, UploadFile, File, Depends, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app import utils
from app.database import models
from app import schemas
from app.dependencies import get_db
from app.settings import settings
from app.schemas.floors import MAX_OVERLAY_SIZE_BYTES, MAX_OVERLAY_SIZE_BYTES_SVG

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

async def _get_overlay(
    id: int,
    db: AsyncSession
) -> models.FloorOverlay:
    overlay = await db.get(models.FloorOverlay, id)
    if not overlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overlay not found"
        )

    return overlay

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

@router.get("/{id}/overlays/{overlay_id}", response_model=schemas.FloorOverlay)
async def get_overlay(
    id: int = Path(description="Floor ID"),
    overlay_id: int = Path(description="The ID of the floor overlay to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a floor overlay by ID."""
    await _raise_404_if_not_found(id, db)

    return await _get_overlay(overlay_id, db)

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

@router.get("/{id}/overlays/{overlay_id}/file", response_class=FileResponse)
async def serve_overlay_file(
    id: int = Path(description="Floor ID"),
    overlay_id: int = Path(description="The ID of the overlay to get the image file for"),
    db: AsyncSession = Depends(get_db)
):
    """Serve the actual overlay image file"""
    await _raise_404_if_not_found(id, db)

    overlay = await _get_overlay(overlay_id, db)
    if not overlay.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file uploaded for this overlay record"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR, overlay.stored_filename)

@router.put("/{id}/overlays/{overlay_id}/file")
async def upload_overlay_file(
    id: int = Path(description="Floor ID"),
    overlay_id: int = Path(description="The ID of the floor to upload the overlay file for"),
    file: UploadFile = File(description="The overlay file to upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload/update the actual overlay image file"""
    await _raise_404_if_not_found(id, db)

    overlay = await _get_overlay(overlay_id, db)

    extension = utils.validate_file_extension(file, True, ".jpg", ".jpeg", ".png", ".svg")
    new_file_path = await utils.store_uploaded_file(
        file,
        settings.FILE_UPLOAD_DIR,
        MAX_OVERLAY_SIZE_BYTES_SVG if extension == ".svg" else MAX_OVERLAY_SIZE_BYTES
    )
    overlay.stored_filename = os.path.split(new_file_path)[-1]
    overlay.original_filename = file.filename

    db.add(overlay)
    await db.commit()

@router.put("/{id}/overlays/{overlay_id}", response_model=schemas.FloorOverlay)
async def update_overlay(
    id: int = Path(description="Floor ID"),
    overlay_id: int = Path(description="The ID of the floor overlay to update"),
    data: schemas.FloorOverlayUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a floor overlay."""
    await _raise_404_if_not_found(id, db)

    overlay = await _get_overlay(overlay_id, db)

    dataDict = data.dict(exclude_unset=True)
    dataDict['extent'] = data.extent.to_wkt()
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(overlay, field, dataDict[field])

    db.add(overlay)
    await db.commit()
    await db.refresh(overlay)

    return overlay

@router.delete("/{id}/overlays/{overlay_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_overlay(
    id: int = Path(description="Floor ID"),
    overlay_id: int = Path(description="The ID of the floor overlay to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a floor overlay by ID"""
    await _raise_404_if_not_found(id, db)

    overlay = await _get_overlay(overlay_id, db)
    await db.delete(overlay)
    await db.commit()


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


#==========================================================================================
# Pano Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/panos/", tags=["Panos"], status_code=status.HTTP_201_CREATED, response_model=schemas.Pano)
async def create_pano(
    id: int = Path(description="The ID of the floor to place the pano on"),
    data: schemas.PanoCreate = Body(description="The new pano to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new pano"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['floor_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    pano = models.Pano(**dataDict)
    db.add(pano)
    await db.commit()
    await db.refresh(pano)

    return pano

@router.get("/{id}/panos/", tags=["Panos"], response_model=list[schemas.Pano])
async def get_panos(
    id: int = Path(description="The ID of the floor to get panos for"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query panos on the specified floor"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Pano).where(models.Pano.floor_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()


#==========================================================================================
# Photo Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/photos/", tags=["Photos"], status_code=status.HTTP_201_CREATED, response_model=schemas.Photo)
async def create_photo(
    id: int = Path(description="The ID of the floor to place the photo on"),
    data: schemas.PhotoCreate = Body(description="The new photo to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new photo"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['floor_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    photo = models.Photo(**dataDict)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return photo

@router.get("/{id}/photos/", tags=["Photos"], response_model=list[schemas.Photo])
async def get_photos(
    id: int = Path(description="The ID of the floor to get photos for"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query photos on the specified floor"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Photo).where(models.Photo.floor_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()
