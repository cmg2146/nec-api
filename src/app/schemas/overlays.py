"""Pydantic models for Surveys"""

from pydantic import BaseModel, Field, validator

from app.schemas._base import BaseSchemaModelInDb
from app.schemas import Extent
from app.schemas.extent import convert_geoalchemy_element

MAX_OVERLAY_SIZE_BYTES = 30*1024*1024 #30MB
# SVGs are intensive to render, so limit file size more
MAX_OVERLAY_SIZE_BYTES_SVG = 10*1024*1024 #10MB

class OverlayBase(BaseModel):
    """Base Pydantic model for an Overlay"""
    extent: Extent = Field(
        description="The geoographic bounding box of the overlay"
    )
    level: int = Field(
        default=1,
        description="The floor level the overlay is on."
    )

    # pydantic validators
    _convert_extent = validator(
        'extent',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class Overlay(OverlayBase, BaseSchemaModelInDb):
    """Pydantic model for a Floor Overlay"""
    survey_id: int = Field(
        description="The survey this overlay belongs to"
    )

    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual image files and the filenames are determined/generated automatically.
    original_filename: str | None = Field(
        description="The uploaded/original name of the overlay image file"
    )

    class Config:
        orm_mode = True

class OverlayCreate(OverlayBase):
    pass

class OverlayUpdate(OverlayBase):
    pass
