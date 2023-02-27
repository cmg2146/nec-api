"""Pydantic models for Photos"""

from pydantic import BaseModel, Field, validator

from app.database.models.photos import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

#==========================================================================================
# Photo
#==========================================================================================
class PhotoBase(BaseModel):
    """Base Pydantic model for a Photo"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    description: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH
    )
    coordinates: Coordinates
    heading: float = Field(
        ge=-180.0,
        le=180.0,
        description="Direction, relative to true north, of the center of the photo, in degrees."
    )
    is_cubic_pano: bool | None = Field(
        default=None,
        description="None - Regular Photo, False - Spherical Pano, True - Cubic Pano"
    )
    custom_marker: str | None = Field(
        default=None,
        max_length=MAX_NAME_LENGTH,
        description="Custom data to associate a photo record with the correct image file."
    )
    # pydantic validators
    _convert_coordinates = validator(
        'coordinates',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class PhotoCreate(PhotoBase):
    pass

class PhotoUpdate(PhotoBase):
    pass

class Photo(PhotoBase, BaseSchemaModelInDb):
    """Pydantic model for a Photo"""
    floor_id: int = Field(
        description="The Id of the floor this photo belongs to."
    )
    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual image files and the filenames are determined/generated automatically.
    original_filename: str | None = Field(
        description="The uploaded/original name of the photo"
    )

    class Config:
        orm_mode = True


#==========================================================================================
# Hotspot
#==========================================================================================
class HotspotBase(BaseModel):
    """Base Pydantic model for a Hotspot"""
    x_coord: float = Field(
        description="Horizontal location of the hotspot in the photo."
    )
    y_coord: float = Field(
        description="Horizontal location of the hotspot in the photo."
    )

class HotspotCreate(HotspotBase):
    asset_id: int | None = Field(
        description="The ID of the asset this hotspot references, if applicable."
    )
    destination_photo_id: int | None = Field(
        description="The ID of the photo this hotspot references, if applicable."
    )

    #TODO: Check that either asset or destination photo is not null

class HotspotUpdate(HotspotBase):
    pass

class Hotspot(HotspotBase, BaseSchemaModelInDb):
    """Pydantic model for a Hotspot"""
    source_photo_id: int = Field(
        description="The Id of the photo this hotspot belongs to."
    )

    class Config:
        orm_mode = True
