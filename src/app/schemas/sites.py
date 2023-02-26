"""Pydantic models for Sites"""

from pydantic import BaseModel, Field, validator

from app.database.models.sites import MAX_NAME_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

class SiteBase(BaseModel):
    """Base Pydantic model for a Site"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    coordinates: Coordinates
    parent_site_id: int | None = Field(
        default=None,
        description="The Id of this site's parent site."
        # TODO: Set example to null
    )

    # pydantic validators
    _convert_coordinates = validator(
        'coordinates',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class Site(SiteBase, BaseSchemaModelInDb):
    """Pydantic model for a Site"""

    class Config:
        orm_mode = True

class SiteCreate(SiteBase):
    pass

class SiteUpdate(SiteBase):
    pass
