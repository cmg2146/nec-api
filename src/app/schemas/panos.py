"""Pydantic models for Photos"""

from pydantic import BaseModel, Field, validator

from app.database.models.photos import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

MAX_PANO_FILE_SIZE_BYTES = 10*1024*1024 #20MB

#==========================================================================================
# Pano
#==========================================================================================
class PanoBase(BaseModel):
    """Base Pydantic model for a Pano"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    description: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH
    )
    coordinates: Coordinates
    heading: float | None = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Direction, relative to true north, of the center of the photo, in degrees."
    )
    custom_marker: str | None = Field(
        default=None,
        max_length=MAX_NAME_LENGTH,
        description="Custom data to associate a photo record with the correct image file."
    )
    level: int = Field(
        default=1,
        description="The floor level the pano is on."
    )

    # pydantic validators
    _convert_coordinates = validator(
        'coordinates',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class PanoCreate(PanoBase):
    pass

class PanooUpdate(PanoBase):
    pass

class Pano(PanoBase, BaseSchemaModelInDb):
    """Pydantic model for a Pano"""
    survey_id: int = Field(
        description="The Id of the survey this pano belongs to."
    )
    # only supports spherical panos right now
    is_cubic_pano: bool = Field(
        description="False - Spherical Pano, True - Cubic Pano"
    )
    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual image files and the filenames are determined/generated automatically.
    original_filename: str | None = Field(
        description="The uploaded/original name of the pano file"
    )

    class Config:
        orm_mode = True


#==========================================================================================
# Hotspot
#==========================================================================================
class HotspotBase(BaseModel):
    """Base Pydantic model for a Hotspot"""
    yaw: float = Field(
        ge=-180.0,
        le=180.0,
        description="Horizontal location of the hotspot in the photo, in degrees."
    )
    pitch: float = Field(
        ge=-90.0,
        le=90.0,
        description="Horizontal location of the hotspot in the photo, in degrees."
    )

class HotspotCreate(HotspotBase):
    asset_id: int | None = Field(
        description="The ID of the asset this hotspot references, if applicable."
    )
    destination_pano_id: int | None = Field(
        description="The ID of the pano this hotspot links to, if applicable."
    )

class HotspotUpdate(HotspotBase):
    pass

class Hotspot(HotspotBase, BaseSchemaModelInDb):
    """Pydantic model for a Hotspot"""
    pano_id: int = Field(
        description="The Id of the pano this hotspot belongs to."
    )

    class Config:
        orm_mode = True
