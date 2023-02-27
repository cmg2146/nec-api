"""Pydantic models for Surveys"""

from datetime import date

from pydantic import BaseModel, Field, validator

from app.database.models.sites import MAX_NAME_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas import Extent
from app.schemas.extent import convert_geoalchemy_element

class FloorBase(BaseModel):
    """Base Pydantic model for a Floor"""
    name: str = Field(max_length=MAX_NAME_LENGTH)

class Floor(FloorBase, BaseSchemaModelInDb):
    """Pydantic model for a Floor"""
    survey_id: int = Field(
        description="The survey this floor belongs to"
    )

    class Config:
        orm_mode = True

class FloorCreate(FloorBase):
    pass

class FloorUpdate(FloorBase):
    pass


class FloorOverlayBase(BaseModel):
    """Base Pydantic model for a Floor Overlay"""
    extent: Extent = Field(
        description="The geoographic bounding box of the overlay"
    )

    # pydantic validators
    _convert_extent = validator(
        'extent',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class FloorOverlay(FloorOverlayBase, BaseSchemaModelInDb):
    """Pydantic model for a Floor Overlay"""
    floor_id: int = Field(
        description="The floor this overlay belongs to"
    )

    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual image files and the filenames are determined/generated automatically.
    original_filename: str | None = Field(
        description="The uploaded/original name of the overlay image file"
    )

    class Config:
        orm_mode = True

class FloorOverlayCreate(FloorOverlayBase):
    pass

class FloorOverlayUpdate(FloorOverlayBase):
    pass
