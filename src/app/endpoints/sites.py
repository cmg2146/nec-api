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
# Create Site
#==========================================================================================
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=schemas.Site)
async def create_site(
    data: schemas.SiteCreate = Body(description="The new site to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new site"""
    dataDict = data.dict()
    dataDict['coordinates'] = data.coordinates.to_wkt()
    site = models.Site(**dataDict)

    # dont allow more than two levels of sites
    if data.parent_site_id:
        grandparent_site_id = await db.scalar(
            select(models.Site.parent_site_id)
            .where(models.Site.id == data.parent_site_id)
        )
        if grandparent_site_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Site exceeds maximum number of 2 hierarchy levels"
            )

    return await crud.create(db, site)

#==========================================================================================
# Query Sites
#==========================================================================================
@router.get("/", response_model=list[schemas.Site])
async def get_sites(
    search: str | None = Query(
        default=None,
        description="Search Field"
    ),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
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
) -> StreamingResponse:
    """Query sites"""
    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = select(models.Site).order_by(desc(sort_by) if sort_desc else sort_by)
    if search:
        query = query.where(models.Site.name.icontains(search, autoescape=True))
    if skip:
        query = query.offset(skip)
    if limit:
        query = query.limit(limit)

    return (await db.scalars(query)).all()

#==========================================================================================
# Get Site
#==========================================================================================
@router.get("/{id}", response_model=schemas.Site)
async def get_site(
    id: int = Path(description="The ID of the site to get"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Retrieve a site by ID."""
    return await crud.get(db, models.Site, id)

#==========================================================================================
# Get Sub-Sites
#==========================================================================================
@router.get("/{id}/sub-sites", response_model=list[schemas.Site])
async def get_sub_sites(
    id: int = Path(description="The ID of the site to get sub sites for"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query sub sites"""
    await crud.raise_if_not_found(db, models.Site, id, "Site does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.Site)
        .where(models.Site.parent_site_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )

    return (await db.scalars(query)).all()

#==========================================================================================
# Update Site
#==========================================================================================
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
    for field in dataDict:
        setattr(site, field, dataDict[field])

    return await crud.update(db, site)

#==========================================================================================
# Delete Site
#==========================================================================================
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(
    id: int = Path(description="The ID of the site to delete"),
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a site by ID"""
    site = await crud.get(db, models.Site, id)

    any_survey = await db.scalar(
        select(models.Survey.id)
        .join(models.Site)
        .where(
            # assumes max 2 level site hierarchy
            (models.Site.parent_site_id == id) |
            (models.Site.id == id)
        )
    )
    if any_survey:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete site because it has associated surveys"
        )

    await crud.delete(db, site)

#==========================================================================================
# Create Survey
#==========================================================================================
@router.post(
    "/{id}/surveys",
    tags=["Surveys"],
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.Survey
)
async def create_survey(
    id: int = Path(description="The ID of the site the survey belongs to"),
    data: schemas.SurveyCreate = Body(description="The new survey to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new survey"""
    await crud.raise_if_not_found(db, models.Site, id, "Site does not exist")

    dataDict = data.dict()
    dataDict['site_id'] = id
    survey = models.Survey(**dataDict)

    return await crud.create(db, survey)

#==========================================================================================
# Get Surveys for Site
#==========================================================================================
@router.get("/{id}/surveys", tags=["Surveys"], response_model=list[schemas.Survey])
async def get_surveys(
    id: int = Path(description="The ID of the site to get surveys for"),
    sort_by: schemas.SortByWithName = Query(
        default=schemas.SortByWithName.NAME,
        description="The field to order results by"
    ),
    sort_direction: schemas.SortDirection = Query(
        default=schemas.SortDirection.ASCENDING
    ),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a site's surveys"""
    await crud.raise_if_not_found(db, models.Site, id, "Site does not exist")

    sort_desc = sort_direction == schemas.SortDirection.DESCENDING
    query = (
        select(models.Survey)
        .where(models.Survey.site_id == id)
        .order_by(desc(sort_by) if sort_desc else sort_by)
    )

    return (await db.scalars(query)).all()
