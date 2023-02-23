"""Module containing asset and related database models"""

from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models._base import BaseDbModel

_ASSET_PROPERTY_NAME_LENGTH = 100

class Asset(BaseDbModel):
    """Asset model

    An asset is an item of interest which occupies a physical point in space
    """
    __tablename__ = "asset"

    name = Column(String(length=100), nullable=False)
    description = Column(String(length=255), nullable=True)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    """The latitude and longitude of the asset."""

    asset_type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False, index=True)
    floor_id = Column(Integer, ForeignKey("floor.id"), nullable=False, index=True)

    asset_type = relationship("AssetType", back_populates="assets")
    asset_properties = relationship("AssetProperty", back_populates="asset")
    floor = relationship("Floor", back_populates="assets")
    asset_hotspots = relationship("Hotspot", back_populates="asset")

class AssetType(BaseDbModel):
    """Asset Type model

    Asset types help distinguish assets from each other
    """
    __tablename__ = "asset_type"

    name = Column(String(length=100), nullable=False)
    description = Column(String(length=255), nullable=True)
    category = Column(String(length=100), nullable=True)
    icon = Column(LargeBinary, nullable=False)

    assets = relationship("Asset", back_populates="asset_type")
    asset_property_names = relationship("AssetPropertyName", back_populates="asset_type")

class AssetPropertyName(BaseDbModel):
    """Asset Property Name model

    Asset property names define the custom information to be stored for assets based on their types.
    For example, an asset of type "Computer" could have one property named "MAC Address" and another
    named "Manufacturer."
    """
    __tablename__ = "asset_property_name"

    name = Column(String(length=_ASSET_PROPERTY_NAME_LENGTH), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False, index=True)

    asset_type = relationship("AssetType", back_populates="asset_property_names")
    asset_properties = relationship("AssetProperty", back_populates="asset_property_name")

class AssetProperty(BaseDbModel):
    """Asset Property model

    Asset properties are the actual, custom information stored for assets.
    """
    __tablename__ = "asset_property"

    name = Column(String(length=_ASSET_PROPERTY_NAME_LENGTH), nullable=False)
    value = Column(String, nullable=False)
    asset_property_name_id = Column(Integer, ForeignKey("asset_property_name.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=False, index=True)

    # NOTE on why there is both a name field and foreign key to the name property: This allows flexibilty
    # when updating property names - we can change names going forward without affecting existing assets,
    # retroactively change existing assets, or both.

    asset_property_name = relationship("AssetPropertyName", back_populates="asset_properties")
    asset = relationship("Asset", back_populates="asset_properties")
