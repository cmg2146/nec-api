"""API Endpoints for Overlays"""

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
from app.schemas.overlays import MAX_OVERLAY_SIZE_BYTES, MAX_OVERLAY_SIZE_BYTES_SVG
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/overlays",
    tags=["Overlays"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Query Overlays
#==========================================================================================
@router.get("/", response_model=list[schemas.Overlay])
async def get_overlays(
    site_id: int | None = Query(
        default=None,
        description="Only return overlays belonging to the specified site"
    ),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.CREATED,
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
    """Query overlays"""
    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = select(models.Overlay).order_by(desc(sort_by) if sort_desc else sort_by)
    if site_id:
        query = query.join(models.Survey).where(models.Survey.site_id == site_id)
    if skip:
        query = query.offset(skip)
    if limit:
        query = query.limit(limit)

    return (await db.scalars(query)).all()

#==========================================================================================
# Get Overlay
#==========================================================================================
@router.get("/{id}", response_model=schemas.Overlay)
async def get_overlay(
    id: int = Path(description="The ID of the overlay to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve an overlay by ID."""
    return await crud.get(db, models.Overlay, id)

#==========================================================================================
# Get Overlay File
#==========================================================================================
@router.get("/{id}/file", response_class=FileResponse)
async def serve_overlay_file(
    id: int = Path(description="The ID of the overlay to get the image file for"),
    db: AsyncSession = Depends(get_db)
):
    """Serve the actual overlay image file"""
    overlay = await crud.get(db, models.Overlay, id)

    if not overlay.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file uploaded for this overlay record"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR, overlay.stored_filename)

#==========================================================================================
# Update Overlay File
#==========================================================================================
@router.put("/{id}/file")
async def upload_overlay_file(
    id: int = Path(description="The ID of the overlay to upload the image file for"),
    file: UploadFile = File(description="The overlay file to upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload/update the actual overlay image file"""
    overlay = await crud.get(db, models.Overlay, id)

    extension = utils.validate_file_extension(file, True, ".jpg", ".jpeg", ".png", ".svg")
    new_file_path = await utils.store_uploaded_file(
        file,
        settings.FILE_UPLOAD_DIR,
        MAX_OVERLAY_SIZE_BYTES_SVG if extension == ".svg" else MAX_OVERLAY_SIZE_BYTES
    )
    overlay.stored_filename = os.path.split(new_file_path)[-1]
    overlay.original_filename = file.filename

    await crud.update(db, overlay)

#==========================================================================================
# Update Overlay
#==========================================================================================
@router.put("/{id}", response_model=schemas.Overlay)
async def update_overlay(
    id: int = Path(description="The ID of the overlay to update"),
    data: schemas.OverlayUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update an overlay."""
    overlay = await crud.get(db, models.Overlay, id)

    dataDict = data.dict(exclude_unset=True)
    dataDict['extent'] = data.extent.to_wkt()
    for field in dataDict:
        setattr(overlay, field, dataDict[field])

    return await crud.update(db, overlay)

#==========================================================================================
# Delete Overlay
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_overlay(
    id: int = Path(description="The ID of the overlay to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete an overlay by ID"""
    await crud.delete(db, models.Overlay, id)
