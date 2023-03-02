"""Pydantic models for Sites"""

from pydantic import BaseModel, Field, validator

from app.database.models.sites import MAX_NAME_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

class SiteBase(BaseModel):
    """Base Pydantic model for a Site"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    coordinates: Coordinates = Field(
        description="The location of the site"
    )
    parent_site_id: int | None = Field(
        default=None,
        description="The Id of this site's parent site, or null if no parent."
    )

    # pydantic validators
    _convert_coordinates = validator(
        'coordinates',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class Site(SiteBase, BaseSchemaModelInDb):
    """Schema model for a Site"""

    class Config:
        orm_mode = True

class SiteCreate(SiteBase):
    """Schema model for creating a site"""
    pass

class SiteUpdate(SiteBase):
    """Schema model for updating a site"""
    pass
