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
from app.schemas.panos import MAX_PANO_FILE_SIZE_BYTES
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/panos",
    tags=["Panos"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Pano Resource Operations
#==========================================================================================
@router.get("/", response_model=list[schemas.Pano])
async def get_panos(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query panos"""
    return await crud.get_all_with_limit(
        db,
        models.Pano,
        skip,
        limit,
        sort_by,
        sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    )

@router.get("/{id}", response_model=schemas.Pano)
async def get_pano(
    id: int = Path(description="The ID of the pano to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a pano by ID."""
    return await crud.get(db, models.Pano, id)

@router.get("/{id}/file", response_class=FileResponse)
async def serve_pano_file(
    id: int = Path(description="The ID of the pano to get the image file for"),
    db: AsyncSession = Depends(get_db)
):
    """Serve the actual pano image file"""
    pano = await crud.get(db, models.Pano, id)
    if not pano.stored_filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file uploaded for this pano record"
        )

    return os.path.join(settings.FILE_UPLOAD_DIR, pano.stored_filename)

@router.put("/{id}/file")
async def upload_pano_file(
    id: int = Path(description="The ID of the pano to upload the image for"),
    file: UploadFile = File(description="The pano file to upload"),
    db: AsyncSession = Depends(get_db)
):
    """Upload/update the actual image file for a pano record"""
    pano = await crud.get(db, models.Pano, id)

    utils.validate_file_extension(file, True, ".jpg", ".jpeg", ".png")
    # TODO: validate aspect ratio is 2:1
    new_file_path = await utils.store_uploaded_file(
        file,
        settings.FILE_UPLOAD_DIR,
        MAX_PANO_FILE_SIZE_BYTES
    )
    pano.stored_filename = os.path.split(new_file_path)[-1]
    pano.original_filename = file.filename

    await crud.update(db, pano)

@router.put("/{id}", response_model=schemas.Pano)
async def update_pano(
    id: int = Path(description="The ID of the pano to update"),
    data: schemas.PanooUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a pano."""
    pano = await crud.get(db, models.Pano, id)

    dataDict = data.dict(exclude_unset=True)
    dataDict['coordinates'] = data.coordinates.to_wkt()
    for field in dataDict:
        setattr(pano, field, dataDict[field])

    return await crud.update(db, pano)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pano(
    id: int = Path(description="The ID of the pano to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a pano by ID"""
    # TODO: Need to delete all of this panos hotspots and any hotspot that links to this pano
    await crud.delete(db, models.Pano, id)


#==========================================================================================
# Hotspot Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/hotspots/", status_code=status.HTTP_201_CREATED, response_model=schemas.Hotspot)
async def create_hotspot(
    id: int = Path(description="The ID of the pano to place the hotspot in"),
    data: schemas.HotspotCreate = Body(description="The new hotspot to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new hotspot"""
    await crud.raise_if_not_found(db, models.Pano, id, "Pano does not exist")

    dataDict = data.dict()
    dataDict['pano_id'] = id
    hotspot = models.Hotspot(**dataDict)

    return await crud.create(db, hotspot)

@router.get("/{id}/hotspots/", response_model=list[schemas.Hotspot])
async def get_hotspots(
    id: int = Path(description="The ID of the pano to get hotspots for"),
    sort_by: schemas.SortBy = Query(default=schemas.SortBy.CREATED, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a pano's hotspots"""
    await crud.raise_if_not_found(db, models.Pano, id, "Pano does not exist")

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Hotspot).where(models.Hotspot.pano_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()

@router.put("/{id}/hotspots/{hotspot_id}", response_model=schemas.Hotspot)
async def update_hotspot(
    id: int = Path(description="Pano ID"),
    hotspot_id: int = Path(description="ID of the hotspot to update"),
    data: schemas.HotspotUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a hotspot."""
    await crud.raise_if_not_found(db, models.Pano, id, "Pano does not exist")

    #check if hotspot exists first
    query = select(models.Hotspot).where(
        models.Hotspot.id == hotspot_id &
        models.Hotspot.pano_id == id
    )
    hotspot = await db.scalar(query)
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotspot not found"
        )

    dataDict = data.dict(exclude_unset=True)
    for field in dataDict:
        setattr(hotspot, field, dataDict[field])

    return await crud.update(db, hotspot)

@router.delete("/{id}/hotspots/{hotspot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotspot(
    id: int = Path(description="Pano ID"),
    hotspot_id: int = Path(description="ID of the hotspot to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a hotspot by ID"""
    await crud.raise_if_not_found(db, models.Pano, id, "Pano does not exist")

    query = select(models.Hotspot).where(
        models.Hotspot.id == hotspot_id &
        models.Hotspot.pano_id == id
    )
    hotspot = await db.scalar(query)
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotspot not found"
        )

    await crud.delete(db, hotspot)
