"""API Endpoints for Photos"""

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
from app.schemas.photos import MAX_PHOTO_FILE_SIZE_BYTES
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/photos",
    tags=["Photos"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
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
    return await crud.get(db, models.Photo, id)

@router.get("/{id}/file", response_class=FileResponse)
async def serve_photo_file(
    id: int = Path(description="The ID of the photo to get the image file for"),
    db: AsyncSession = Depends(get_db)
):
    """Serve the actual photo file"""
    photo = await crud.get(db, models.Photo, id)
    if not photo.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file uploaded for this photo record"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR, photo.stored_filename)

@router.put("/{id}/file")
async def upload_photo_file(
    id: int = Path(description="The ID of the photo to upload the image for"),
    file: UploadFile = File(description="The actual photo to upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload/update the actual image file for a photo record"""
    photo = await crud.get(db, models.Photo, id)

    utils.validate_file_extension(file, True, ".jpg", ".jpeg", ".png")
    new_file_path = await utils.store_uploaded_file(
        file,
        settings.FILE_UPLOAD_DIR,
        MAX_PHOTO_FILE_SIZE_BYTES
    )
    photo.stored_filename = os.path.split(new_file_path)[-1]
    photo.original_filename = file.filename

    db.add(photo)
    await db.commit()

@router.put("/{id}", response_model=schemas.Photo)
async def update_photo(
    id: int = Path(description="The ID of the photo to update"),
    data: schemas.PhotoUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a photo."""
    photo = await crud.get(db, models.Photo, id)

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
    photo = await crud.get(db, models.Photo, id)
    await db.delete(photo)
    await db.commit()
