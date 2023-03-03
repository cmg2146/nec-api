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
# Query photos
#==========================================================================================
@router.get("/", response_model=list[schemas.Photo])
async def get_photos(
    search: str | None = Query(
        default=None,
        description="Search Field"
    ),
    site_id: int | None = Query(
        default=None,
        description="Only return photos belonging to the specified site"
    ),
    c_params: schemas.CommonQueryParams = Depends(schemas.CommonQueryParams),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query photos"""
    query = (
        select(models.Photo)
        .order_by(desc(c_params.sort_by) if c_params.sort_desc else c_params.sort_by)
    )
    if search:
        query = query.where(models.Photo.name.icontains(search, autoescape=True))
    if site_id:
        query = query.join(models.Survey).where(models.Survey.site_id == site_id)
    if c_params.skip:
        query = query.offset(c_params.skip)
    if c_params.limit:
        query = query.limit(c_params.limit)

    return (await db.scalars(query)).all()

#==========================================================================================
# Get photo
#==========================================================================================
@router.get("/{id}", response_model=schemas.Photo)
async def get_photo(
    id: int = Path(description="The ID of the photo to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a photo by ID."""
    return await crud.get(db, models.Photo, id)

#==========================================================================================
# Get photo file
#==========================================================================================
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

#==========================================================================================
# Upload photo file
#==========================================================================================
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

    await crud.update(db, photo)

#==========================================================================================
# Update photo
#==========================================================================================
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
    for field in dataDict:
        setattr(photo, field, dataDict[field])

    return await crud.update(db, photo)

#==========================================================================================
# Delete photo
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(
    id: int = Path(description="The ID of the photo to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a photo by ID"""
    await crud.delete(db, models.Photo, id)
