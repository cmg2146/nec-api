"""API Endpoints for Surveys"""

from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/surveys",
    tags=["Surveys"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

async def _get(
    id: int,
    db: AsyncSession
) -> models.Survey:
    survey = await db.get(models.Survey, id)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )

    return survey

async def _raise_404_if_not_found(
    id: int,
    db: AsyncSession
):
    query = select(models.Survey.id).where(models.Survey.id == id)
    survey = await db.scalar(query)
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey not found"
        )

#==========================================================================================
# Survey Resource Operations
#==========================================================================================
@router.get("/", response_model=list[schemas.Survey])
async def get_surveys(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query surveys"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Survey).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.Survey)
async def get_survey(
    id: int = Path(description="The ID of the survey to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a survey by ID."""
    return await _get(id, db)

@router.put("/{id}", response_model=schemas.Survey)
async def update_survey(
    id: int = Path(description="The ID of the survey to update"),
    data: schemas.SurveyUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a survey."""
    survey = await _get(id, db)

    dataDict = data.dict(exclude_unset=True)
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(survey, field, dataDict[field])

    db.add(survey)
    await db.commit()
    await db.refresh(survey)

    return survey

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_survey(
    id: int = Path(description="The ID of the survey to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a survey by ID"""
    survey = await _get(id, db)
    await db.delete(survey)
    await db.commit()


#==========================================================================================
# Overlay Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/overlays/", tags=["Overlays"], status_code=status.HTTP_201_CREATED, response_model=schemas.Overlay)
async def create_overlay(
    id: int = Path(description="The ID of the survey the overlay belongs to"),
    data: schemas.OverlayCreate = Body(description="The new overlay to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new overlay"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['extent'] = data.extent.to_wkt()
    dataDict['created'] = datetime.utcnow()

    overlay = models.Overlay(**dataDict)
    db.add(overlay)
    await db.commit()
    await db.refresh(overlay)

    return overlay

@router.get("/{id}/overlays/", tags=["Overlays"], response_model=list[schemas.Overlay])
async def get_overlays(
    id: int = Path(description="The ID of the survey to get overlays for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortBy = Query(default=schemas.SortBy.CREATED, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's overlays"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Overlay).where(models.Overlay.survey_id == id).order_by(sort_by)
    if level is not None:
        query = query.where(models.Overlay.level == level)

    result = await db.scalars(query)

    return result.all()


#==========================================================================================
# Asset Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/assets/", tags=["Assets"], status_code=status.HTTP_201_CREATED, response_model=schemas.Asset)
async def create_asset(
    id: int = Path(description="The ID of the survey the asset belongs to"),
    data: schemas.AssetCreate = Body(description="The new asset to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new asset"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    asset = models.Asset(**dataDict)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    return asset

@router.get("/{id}/assets/", tags=["Assets"], response_model=list[schemas.Asset])
async def get_assets(
    id: int = Path(description="The ID of the survey to get assets for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's assets"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Asset).where(models.Asset.survey_id == id).order_by(sort_by)
    if level is not None:
        query = query.where(models.Asset.level == level)

    result = await db.scalars(query)

    return result.all()


#==========================================================================================
# Pano Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/panos/", tags=["Panos"], status_code=status.HTTP_201_CREATED, response_model=schemas.Pano)
async def create_pano(
    id: int = Path(description="The ID of the survey the pano belongs to"),
    data: schemas.PanoCreate = Body(description="The new pano to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new pano"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    pano = models.Pano(**dataDict)
    db.add(pano)
    await db.commit()
    await db.refresh(pano)

    return pano

@router.get("/{id}/panos/", tags=["Panos"], response_model=list[schemas.Pano])
async def get_panos(
    id: int = Path(description="The ID of the survey to get panos for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's panos"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Pano).where(models.Pano.survey_id == id).order_by(sort_by)
    if level is not None:
        query = query.where(models.Pano.level == level)

    result = await db.scalars(query)

    return result.all()


#==========================================================================================
# Photo Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/photos/", tags=["Photos"], status_code=status.HTTP_201_CREATED, response_model=schemas.Photo)
async def create_photo(
    id: int = Path(description="The ID of the survey the photo belongs to"),
    data: schemas.PhotoCreate = Body(description="The new photo to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new photo"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    photo = models.Photo(**dataDict)
    db.add(photo)
    await db.commit()
    await db.refresh(photo)

    return photo

@router.get("/{id}/photos/", tags=["Photos"], response_model=list[schemas.Photo])
async def get_photos(
    id: int = Path(description="The ID of the survey to get photos for"),
    level: int = Query(default=None, description="Limit results to this floor level"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's photos"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Photo).where(models.Photo.survey_id == id).order_by(sort_by)
    if level is not None:
        query = query.where(models.Photo.level == level)

    result = await db.scalars(query)

    return result.all()
