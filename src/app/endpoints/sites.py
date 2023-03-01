"""API Endpoints for Sites"""

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db
from app.endpoints.helpers import crud

router = APIRouter(
    prefix="/sites",
    tags=["Sites"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

#==========================================================================================
# Site Resource Operations
#==========================================================================================
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Site)
async def create_site(
    data: schemas.SiteCreate = Body(description="The new site to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new site"""
    dataDict = data.dict()
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['created'] = datetime.utcnow()

    site = models.Site(**dataDict)
    db.add(site)
    await db.commit()
    await db.refresh(site)

    return site

@router.get("/", response_model=list[schemas.Site])
async def get_sites(
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    skip: int = Query(default=0, description="Skip the specified number of items (for pagination)"),
    limit: int = Query(default=100, description="Max number of results"),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """Query sites"""
    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Site).order_by(sort_by).offset(skip).limit(limit)
    result = await db.scalars(query)

    return result.all()

@router.get("/{id}", response_model=schemas.Site)
async def get_site(
    id: int = Path(description="The ID of the site to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a site by ID."""
    return await crud.get(db, models.Site, id)

@router.get("/{id}/sub-sites", response_model=list[schemas.Site])
async def get_sub_sites(
    id: int = Path(description="The ID of the site to get sub sites for"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query sub sites"""
    await crud.raise_if_not_found(db, models.Site, id, "Site does not exist")

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Site).where(models.Site.parent_site_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()

@router.put("/{id}", response_model=schemas.Site)
async def update_site(
    id: int = Path(description="The ID of the site to update"),
    data: schemas.SiteUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a site."""
    site = await crud.get(db, models.Site, id)

    dataDict = data.dict(exclude_unset=True)
    dataDict['coordinates'] = data.coordinates.to_wkt()
    dataDict['modified'] = datetime.utcnow()

    for field in dataDict:
        setattr(site, field, dataDict[field])

    db.add(site)
    await db.commit()
    await db.refresh(site)

    return site

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    id: int = Path(description="The ID of the site to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a site by ID"""
    site = await crud.get(db, models.Site, id)

    # TODO: Need to delete all sub-sites too. appears like default SQLAlchemy behavior
    # sets the foreign key to null.
    await db.delete(site)
    await db.commit()


#==========================================================================================
# Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/surveys", tags=["Surveys"], status_code=status.HTTP_201_CREATED, response_model=schemas.Survey)
async def create_survey(
    id: int = Path(description="The ID of the site the survey belongs to"),
    data: schemas.SurveyCreate = Body(description="The new survey to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new survey"""
    await crud.raise_if_not_found(db, models.Site, id, "Site does not exist")

    dataDict = data.dict()
    dataDict['site_id'] = id
    dataDict['created'] = datetime.utcnow()

    survey = models.Survey(**dataDict)
    db.add(survey)
    await db.commit()
    await db.refresh(survey)

    return survey

@router.get("/{id}/surveys", tags=["Surveys"], response_model=list[schemas.Survey])
async def get_surveys(
    id: int = Path(description="The ID of the site to get surveys for"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a site's surveys"""
    await crud.raise_if_not_found(db, models.Site, id, "Site does not exist")

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Survey).where(models.Survey.site_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()
