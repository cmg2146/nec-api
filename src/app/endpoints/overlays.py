"""API Endpoints for Floor Overlays"""

from datetime import datetime

from fastapi import APIRouter, Body, Path, Query, Depends, status, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import models
from app import schemas
from app.dependencies import get_db

router = APIRouter(
    prefix="/overlays",
    tags=["overlays"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)

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
    overlay = await db.get(models.FloorOverlay, id)
    if not overlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overlay not found"
        )

    return overlay

@router.put("/{id}", response_model=schemas.FloorOverlay)
async def update_overlay(
    id: int = Path(description="The ID of the floor overlay to update"),
    data: schemas.FloorOverlayUpdate = Body(description="The data to update"),
    db: AsyncSession = Depends(get_db)
) -> any:
    """Update a floor overlay."""
    overlay = await db.get(models.FloorOverlay, id)
    if not overlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overlay not found"
        )

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
    overlay = await db.get(models.FloorOverlay, id)
    if not overlay:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Overlay not found"
        )

    await db.delete(overlay)
    await db.commit()
