"""API Endpoints for Floor Overlays"""

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
    prefix="/overlays",
    tags=["Overlays"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

async def _get(
    id: int,
    db: AsyncSession
) -> models.FloorOverlay:
    overlay = await db.get(models.Survey, id)
    if not overlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overlay not found"
        )

    return overlay

#==========================================================================================
# Floor Overlay Resource Operations
#==========================================================================================
@router.get("/", response_model=list[schemas.FloorOverlay])
async def get_overlays(
    sort_by: schemas.SortBy = Query(default=schemas.SortBy.CREATED, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query floor overlays"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.FloorOverlay).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.FloorOverlay)
async def get_overlay(
    id: int = Path(description="The ID of the floor overlay to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a floor overlay by ID."""
    return await _get(id, db)

@router.get("/{id}/file", response_class=FileResponse)
async def serve_overlay_file(
    id: int = Path(description="The ID of the overlay to get the image file for"),
    db: AsyncSession = Depends(get_db)
):
    """Serve the actual overlay image file"""
    overlay = await _get(id, db)

    if not overlay.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file uploaded for this overlay record"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR, overlay.stored_filename)

@router.put("/{id}/file")
async def upload_asset_type_icon_file(
    id: int = Path(description="The ID of the floor to upload the overlay file for"),
    file: UploadFile = File(description="The overlay file to upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload/update the actual overlay image file"""
    overlay = await _get(id, db)

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

@router.put("/{id}", response_model=schemas.FloorOverlay)
async def update_overlay(
    id: int = Path(description="The ID of the floor overlay to update"),
    data: schemas.FloorOverlayUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a floor overlay."""
    overlay = await _get(id, db)

    dataDict = data.dict(exclude_unset=True)
    dataDict['extent'] = data.extent.to_wkt()
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(overlay, field, dataDict[field])

    db.add(overlay)
    await db.commit()
    await db.refresh(overlay)

    return overlay

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_overlay(
    id: int = Path(description="The ID of the floor overlay to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a floor overlay by ID"""
    overlay = await _get(id, db)
    await db.delete(overlay)
    await db.commit()
