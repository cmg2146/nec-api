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
    site = await db.scalar(query)
    if not site:
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
# Sub-Resource Operations
#==========================================================================================
@router.post("/{id}/floors", tags=["Floors"], status_code=status.HTTP_201_CREATED, response_model=schemas.Floor)
async def create_floor(
    id: int = Path(description="The ID of the survey the floor belongs to"),
    data: schemas.FloorCreate = Body(description="The new floor to create"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Create a new floor"""
    await _raise_404_if_not_found(id, db)

    dataDict = data.dict()
    dataDict['survey_id'] = id
    dataDict['created'] = datetime.utcnow()

    floor = models.Floor(**dataDict)
    db.add(floor)
    await db.commit()
    await db.refresh(floor)

    return floor

@router.get("/{id}/floors", tags=["Floors"], response_model=list[schemas.Floor])
async def get_floors(
    id: int = Path(description="The ID of the survey to get floors for"),
    sort_by: schemas.SortByWithName = Query(default=schemas.SortByWithName.NAME, description="The field to order results by"),
    sort_direction: schemas.SortDirection = Query(default=schemas.SortDirection.ASCENDING),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Query a survey's floors"""
    await _raise_404_if_not_found(id, db)

    if sort_direction == schemas.SortDirection.DESCENDING:
        sort_by = desc(sort_by)

    query = select(models.Floor).where(models.Floor.survey_id == id).order_by(sort_by)
    result = await db.scalars(query)

    return result.all()
