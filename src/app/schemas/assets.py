"""Pydantic models for Assets"""

from pydantic import BaseModel, Field, validator

from app.database.models.assets import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

MAX_ICON_FILE_SIZE_BYTES = 10*1024 #10KB

#==========================================================================================
# Asset
#==========================================================================================
class AssetBase(BaseModel):
    """Base Pydantic model for an Asset"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    description: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH
    )
    coordinates: Coordinates = Field(
        description="The location of the asset"
    )
    asset_type_id: int = Field(
        description="The Id of this asset's type.",
        example=1
    )
    level: int = Field(
        description="The floor level the asset is on.",
        example=1
    )

    # pydantic validators
    _convert_coordinates = validator(
        'coordinates',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class AssetCreate(AssetBase):
    """Schema model for creating an asset"""
    pass

class AssetUpdate(AssetBase):
    """Schema model for updating an asset"""
    pass

class Asset(AssetBase, BaseSchemaModelInDb):
    """Schema model for an Asset"""
    survey_id: int = Field(
        description="The Id of the survey this asset belongs to."
    )

    class Config:
        orm_mode = True


#==========================================================================================
# Asset Property
#==========================================================================================
class AssetPropertyBase(BaseModel):
    """Base Pydantic model for an Asset Property"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    value: str

class AssetPropertyCreate(AssetPropertyBase):
    """Schema model for creating an asset property"""
    pass

class AssetPropertyUpdate(AssetPropertyBase):
    """Schema model for updating an asset property"""
    pass

class AssetProperty(AssetPropertyBase, BaseSchemaModelInDb):
    """Schema model for an Asset Property"""
    asset_id: int = Field(
        description="The ID of the asset this property belongs to."
    )

    class Config:
        orm_mode = True


#==========================================================================================
# Asset Property Name
#==========================================================================================
class AssetPropertyNameBase(BaseModel):
    """Base Pydantic model for an Asset Property Name"""
    name: str = Field(max_length=MAX_NAME_LENGTH)

class AssetPropertyNameCreate(AssetPropertyNameBase):
    """Schema model for creating an asset property name"""
    pass

class AssetPropertyNameUpdate(AssetPropertyNameBase):
    """Schema model for updating an asset property name"""
    pass

class AssetPropertyName(AssetPropertyNameBase, BaseSchemaModelInDb):
    """Schema model for an Asset Property Name"""
    asset_type_id: int = Field(
        description="The ID of the asset type this property is associated with."
    )

    class Config:
        orm_mode = True

#==========================================================================================
# Asset Type
#==========================================================================================
class AssetTypeBase(BaseModel):
    """Base Pydantic model for an Asset Type"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    description: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH
    )
    category: str | None = Field(
        default=None,
        max_length=MAX_NAME_LENGTH
    )

class AssetTypeCreate(AssetTypeBase):
    """Schema model for creating an asset type"""
    pass

class AssetTypeUpdate(AssetTypeBase):
    """Schema model for updating an asset type"""
    pass

class AssetType(AssetTypeBase, BaseSchemaModelInDb):
    """Schema model for an Asset Type"""

    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual icon file and the filenames are determined/generated automatically.
    original_icon_filename: str | None = Field(
        description="The uploaded/original name of the icon file"
    )

    class Config:
        orm_mode = True
