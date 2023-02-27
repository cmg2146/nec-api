"""API Endpoints for Photos"""

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
    prefix="/photos",
    tags=["Photos"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

async def _get(
    id: int,
    db: AsyncSession
) -> models.Photo:
    photo = await db.get(models.Photo, id)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

    return photo

async def _raise_404_if_not_found(
    id: int,
    db: AsyncSession
):
    query = select(models.Photo.id).where(models.Photo.id == id)
    photo = await db.scalar(query)
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )

#==========================================================================================
# Photo Resource Operations
#==========================================================================================
@router.get("/", response_model=list[schemas.Photo])
async def get_photos(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query photos"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Photo).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.Photo)
async def get_photo(
    id: int = Path(description="The ID of the photo to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a photo by ID."""
    return await _get(id, db)

@router.get("/{id}", response_class=FileResponse)
async def serve_photo_file(
    id: int = Path(description="The ID of the photo to get the image file for"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Serve the actual photo file"""
    photo = await _get(id, db)

    if not photo.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file uploaded for this photo record"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR.absolute, photo.stored_filename)

@router.put("/{id}", response_model=schemas.Photo)
async def update_photo(
    id: int = Path(description="The ID of the photo to update"),
    data: schemas.PhotoUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a photo."""
    photo = await _get(id, db)

    dataDict = data.dict(exclude_unset=True)
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(photo, field, dataDict[field])

    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return photo

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    id: int = Path(description="The ID of the photo to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a photo by ID"""
    photo = await _get(id, db)

    # TODO: Need to delete all of this photos hotspots and any hotspot that links to this photo
    await db.delete(photo)
    await db.commit()


#==========================================================================================
# Hotspot Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/hotspots/", status_code=status.HTTP_201_CREATED, response_model=schemas.Hotspot)
async def create_hotspot(
    id: int = Path(description="The ID of the photo to place the hotspot in"),
    data: schemas.HotspotCreate = Body(description="The new hotspot to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new hotspot"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['source_photo_id'] = id
    dataDict['created'] = datetime.utcnow()

    hotspot = models.Hotspot(**dataDict)
    db.add(hotspot)
    await db.commit()
    await db.refresh(hotspot)

    return hotspot

@router.get("/{id}/hotspots/", response_model=list[schemas.Hotspot])
async def get_hotspots(
    id: int = Path(description="The ID of the photo to get hotspots for"),
    sort_by: schemas.SortBy = Query(default=schemas.SortBy.CREATED, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a photo's hotspots"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Hotspot).where(models.Hotspot.source_photo_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()

@router.put("/{id}/hotspots/{hotspot_id}", response_model=schemas.Hotspot)
async def update_hotspot(
    id: int = Path(description="Photo ID"),
    hotspot_id: int = Path(description="ID of the hotspot to update"),
    data: schemas.HotspotUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a hotspot."""
    await _raise_404_if_not_found(id, db)

    #check if hotspot exists first
    query = select(models.Hotspot).where(
        models.Hotspot.id == hotspot_id &
        models.Hotspot.source_photo_id == id
    )
    hotspot = await db.scalar(query)
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotspot not found"
        )

    dataDict = data.dict(exclude_unset=True)
    dataDict['modified'] = datetime.utcnow()
    for field in dataDict:
        setattr(hotspot, field, dataDict[field])

    db.add(hotspot)
    await db.commit()
    await db.refresh(hotspot)

    return hotspot

@router.delete("/{id}/hotspots/{hotspot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotspot(
    id: int = Path(description="Photo ID"),
    hotspot_id: int = Path(description="ID of the hotspot to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a hotspot by ID"""
    await _raise_404_if_not_found(id, db)

    query = select(models.Hotspot).where(
        models.Hotspot.id == hotspot_id &
        models.Hotspot.source_photo_id == id
    )
    hotspot = await db.scalar(query)
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotspot not found"
        )

    await db.delete(hotspot)
    await db.commit()
