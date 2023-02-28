"""Pydantic models for Photos"""

from pydantic import BaseModel, Field, validator

from app.database.models.photos import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

MAX_PHOTO_FILE_SIZE_BYTES = 20*1024*1024 #20MB

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
        description="The floor level the photo is on."
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
    survey_id: int = Field(
        description="The Id of the survey this photo belongs to."
    )
    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual image files and the filenames are determined/generated automatically.
    original_filename: str | None = Field(
        description="The uploaded/original name of the photo"
    )

    class Config:
        orm_mode = True
