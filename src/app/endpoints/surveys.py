"""API Endpoints for Surveys"""

from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/surveys",
    tags=["Surveys"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Query Surveys
#==========================================================================================
@router.get("/", response_model=list[schemas.Survey])
async def get_surveys(
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    skip: int = Query(
        default=0,
        description="Skip the specified number of items (for pagination)"
    ),
    limit: int = Query(
        default=100,
        description="Max number of results"
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query surveys"""
    return await crud.get_all_with_limit(
        db,
        models.Survey,
        skip,
        limit,
        sort_by,
        sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    )

#==========================================================================================
# Get Survey
#==========================================================================================
@router.get("/{id}", response_model=schemas.Survey)
async def get_survey(
    id: int = Path(description="The ID of the survey to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a survey by ID."""
    return await crud.get(db, models.Survey, id)

#==========================================================================================
# Update Survey
#==========================================================================================
@router.put("/{id}", response_model=schemas.Survey)
async def update_survey(
    id: int = Path(description="The ID of the survey to update"),
    data: schemas.SurveyUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a survey."""
    survey = await crud.get(db, models.Survey, id)

    dataDict = data.dict(exclude_unset=True)
    for field in dataDict:
        setattr(survey, field, dataDict[field])

    return await crud.update(db, survey)

#==========================================================================================
# Delete Survey
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(
    id: int = Path(description="The ID of the survey to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a survey by ID"""
    await crud.delete(db, models.Survey, id)

#==========================================================================================
# Create Overlay
#==========================================================================================
@router.post(
    "/{id}/overlays/",
    tags=["Overlays"],
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Overlay
)
async def create_overlay(
    id: int = Path(description="The ID of the survey the overlay belongs to"),
    data: schemas.OverlayCreate = Body(description="The new overlay to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new overlay.

    Use the PUT /overlays/{id}/file endpoint to upload an overlay file after creating
    the record.
    """
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['extent'] = data.extent.to_wkt()
    overlay = models.Overlay(**dataDict)

    return await crud.create(db, overlay)

#==========================================================================================
# Get Overlays for Survey
#==========================================================================================
@router.get("/{id}/overlays/", tags=["Overlays"], response_model=list[schemas.Overlay])
async def get_overlays(
    id: int = Path(description="The ID of the survey to get overlays for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortBy = Query(
        default=schemas.SortBy.CREATED,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's overlays"""
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.Overlay)
        .where(models.Overlay.survey_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )
    if level is not None:
        query = query.where(models.Overlay.level == level)

    return (await db.scalars(query)).all()

#==========================================================================================
# Create Asset
#==========================================================================================
@router.post(
    "/{id}/assets/",
    tags=["Assets"],
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Asset
)
async def create_asset(
    id: int = Path(description="The ID of the survey the asset belongs to"),
    data: schemas.AssetCreate = Body(description="The new asset to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new asset"""
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    asset = models.Asset(**dataDict)

    return await crud.create(db, asset)

#==========================================================================================
# Get Assets for Survey
#==========================================================================================
@router.get("/{id}/assets/", tags=["Assets"], response_model=list[schemas.Asset])
async def get_assets(
    id: int = Path(description="The ID of the survey to get assets for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's assets"""
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.Asset)
        .where(models.Asset.survey_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )
    if level is not None:
        query = query.where(models.Asset.level == level)

    return (await db.scalars(query)).all()

#==========================================================================================
# Create Pano
#==========================================================================================
@router.post(
    "/{id}/panos/",
    tags=["Panos"],
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Pano
)
async def create_pano(
    id: int = Path(description="The ID of the survey the pano belongs to"),
    data: schemas.PanoCreate = Body(description="The new pano to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new pano.

    Use the PUT /panos/{id}/file endpoint to upload the actual pano file after
    creating the record.
    """
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    pano = models.Pano(**dataDict)

    return await crud.create(db, pano)

#==========================================================================================
# Get Panos for Survey
#==========================================================================================
@router.get("/{id}/panos/", tags=["Panos"], response_model=list[schemas.Pano])
async def get_panos(
    id: int = Path(description="The ID of the survey to get panos for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's panos"""
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.Pano)
        .where(models.Pano.survey_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )
    if level is not None:
        query = query.where(models.Pano.level == level)

    return (await db.scalars(query)).all()


#==========================================================================================
# Create Photo
#==========================================================================================
@router.post(
    "/{id}/photos/",
    tags=["Photos"],
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Photo
)
async def create_photo(
    id: int = Path(description="The ID of the survey the photo belongs to"),
    data: schemas.PhotoCreate = Body(description="The new photo to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new photo.

    Use the PUT /photos/{id}/file endpoint to upload the actual photo file after
    creating the record.
    """
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    photo = models.Photo(**dataDict)

    return await crud.create(db, photo)

#==========================================================================================
# Get Photos for Survey
#==========================================================================================
@router.get("/{id}/photos/", tags=["Photos"], response_model=list[schemas.Photo])
async def get_photos(
    id: int = Path(description="The ID of the survey to get photos for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's photos"""
    await crud.raise_if_not_found(db, models.Survey, id, "Survey does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.Photo)
        .where(models.Photo.survey_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )
    if level is not None:
        query = query.where(models.Photo.level == level)

    return (await db.scalars(query)).all()
