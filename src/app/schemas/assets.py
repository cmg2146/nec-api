"""Pydantic models for Assets"""

from pydantic import BaseModel, Field, validator

from app.database.models.assets import MAX_NAME_LENGTH, MAX_DESCRIPTION_LENGTH
from app.schemas._base import BaseSchemaModelInDb
from app.schemas.coordinates import Coordinates, convert_geoalchemy_element

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
    coordinates: Coordinates
    asset_type_id: int = Field(
        description="The Id of this asset's type."
    )

    # pydantic validators
    _convert_coordinates = validator(
        'coordinates',
        pre=True,
        allow_reuse=True
    )(convert_geoalchemy_element)

class AssetCreate(AssetBase):
    pass

class AssetUpdate(AssetBase):
    pass

class Asset(AssetBase, BaseSchemaModelInDb):
    """Pydantic model for an Asset"""
    floor_id: int = Field(
        description="The Id of the floor this asset belongs to."
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
    pass

class AssetPropertyUpdate(AssetPropertyBase):
    pass

class AssetProperty(AssetPropertyBase, BaseSchemaModelInDb):
    """Pydantic model for an Asset Property"""
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
    pass

class AssetPropertyNameUpdate(AssetPropertyNameBase):
    pass

class AssetPropertyName(AssetPropertyNameBase, BaseSchemaModelInDb):
    """Pydantic model for an Asset Property Name"""
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
    pass

class AssetTypeUpdate(AssetTypeBase):
    pass

class AssetType(AssetTypeBase, BaseSchemaModelInDb):
    """Pydantic model for an Asset Type"""

    # File names are not "user" configurable - there is a separate endpoint to upload the
    # actual icon file and the filenames are determined/generated automatically.
    original_icon_filename: str | None = Field(
        description="The uploaded/original name of the icon file"
    )

    class Config:
        orm_mode = True
