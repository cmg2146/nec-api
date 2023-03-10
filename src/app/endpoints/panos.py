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
# Query panos
#==========================================================================================
@router.get("/", response_model=list[schemas.Pano])
async def get_panos(
    search: str | None = Query(
        default=None,
        description="Search Field"
    ),
    site_id: int | None = Query(
        default=None,
        description="Only return panos belonging to the specified site"
    ),
    c_params: schemas.CommonQueryParams = Depends(schemas.CommonQueryParams),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query panos"""
    query = (
        select(models.Pano)
        .order_by(desc(c_params.sort_by) if c_params.sort_desc else c_params.sort_by)
    )
    if search:
        query = query.where(models.Pano.name.icontains(search, autoescape=True))
    if site_id:
        query = query.join(models.Survey).where(models.Survey.site_id == site_id)
    if c_params.skip:
        query = query.offset(c_params.skip)
    if c_params.limit:
        query = query.limit(c_params.limit)

    return (await db.scalars(query)).all()

#==========================================================================================
# Get pano
#==========================================================================================
@router.get("/{id}", response_model=schemas.Pano)
async def get_pano(
    id: int = Path(description="The ID of the pano to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a pano by ID."""
    return await crud.get(db, models.Pano, id)

#==========================================================================================
# Get Pano File
#==========================================================================================
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

#==========================================================================================
# Upload pano file
#==========================================================================================
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

#==========================================================================================
# Update pano
#==========================================================================================
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

#==========================================================================================
# Delete pano
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pano(
    id: int = Path(description="The ID of the pano to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a pano by ID"""
    await crud.delete(db, models.Pano, id)


#==========================================================================================
# Create Hotspot
#==========================================================================================
@router.post(
    "/{id}/hotspots/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Hotspot
)
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

#==========================================================================================
# Get Pano's Hotspots
#==========================================================================================
@router.get("/{id}/hotspots/", response_model=list[schemas.Hotspot])
async def get_hotspots(
    id: int = Path(description="The ID of the pano to get hotspots for"),
    c_params: schemas.CommonQueryParams = Depends(schemas.CommonQueryParams),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a pano's hotspots"""
    await crud.raise_if_not_found(db, models.Pano, id, "Pano does not exist")

    query = select(models.Hotspot).where(models.Hotspot.pano_id == id)

    # hotspots dont support name yet. TODO: populate name from asset or pano.
    if c_params.sort_by == schemas.SortBy.NAME:
        sort_by_param = schemas.SortBy.ID
    else:
        sort_by_param = c_params.sort_by

    query = query.order_by(desc(sort_by_param) if c_params.sort_desc else sort_by_param)
    if c_params.skip:
        query = query.offset(c_params.skip)
    if c_params.limit:
        query = query.limit(c_params.limit)

    return (await db.scalars(query)).all()

#==========================================================================================
# Update Hotspot
#==========================================================================================
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
    hotspot = await db.scalar(
        select(models.Hotspot)
        .where(
            (models.Hotspot.id == hotspot_id) &
            (models.Hotspot.pano_id == id)
        )
    )
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotspot not found"
        )

    dataDict = data.dict(exclude_unset=True)
    for field in dataDict:
        setattr(hotspot, field, dataDict[field])

    return await crud.update(db, hotspot)

#==========================================================================================
# Delete Hotspot
#==========================================================================================
@router.delete("/{id}/hotspots/{hotspot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hotspot(
    id: int = Path(description="Pano ID"),
    hotspot_id: int = Path(description="ID of the hotspot to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a hotspot by ID"""
    await crud.raise_if_not_found(db, models.Pano, id, "Pano does not exist")

    hotspot = await db.scalar(
        select(models.Hotspot)
        .where(
            (models.Hotspot.id == hotspot_id) &
            (models.Hotspot.pano_id == id)
        )
    )
    if not hotspot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotspot not found"
        )

    await crud.delete(db, hotspot)
