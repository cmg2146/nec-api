"""Module containing asset and related database models"""

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models import BaseDbModel

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 255

class Asset(BaseDbModel):
    """Asset model

    An asset is an item of interest which occupies a physical point in space
    """
    __tablename__ = "asset"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    description = Column(String(length=MAX_DESCRIPTION_LENGTH), nullable=True)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False)
    """The latitude and longitude of the asset."""

    asset_type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False, index=True)
    floor_id = Column(Integer, ForeignKey("floor.id"), nullable=False, index=True)

    asset_type = relationship("AssetType", back_populates="assets", lazy="raise")
    asset_properties = relationship("AssetProperty", back_populates="asset", lazy="raise")
    floor = relationship("Floor", back_populates="assets", lazy="raise")
    asset_hotspots = relationship("Hotspot", back_populates="asset", lazy="raise")

class AssetType(BaseDbModel):
    """Asset Type model

    Asset types help distinguish assets from each other
    """
    __tablename__ = "asset_type"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    description = Column(String(length=MAX_DESCRIPTION_LENGTH), nullable=True)
    category = Column(String(length=MAX_NAME_LENGTH), nullable=True)
    original_icon_filename = Column(String(length=255), nullable=True)
    """Original or uploaded filename of the icon file."""
    stored_icon_filename = Column(String(length=255), nullable=True)
    """Icon filename stored on disk."""

    assets = relationship("Asset", back_populates="asset_type", lazy="raise")
    asset_property_names = relationship("AssetPropertyName", back_populates="asset_type", lazy="raise")

class AssetProperty(BaseDbModel):
    """Asset Property model

    Asset properties are the actual, custom information stored for assets.
    """
    __tablename__ = "asset_property"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    value = Column(String, nullable=False)
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=False, index=True)

    asset = relationship("Asset", back_populates="asset_properties", lazy="raise")

class AssetPropertyName(BaseDbModel):
    """Asset Property Name model

    Asset property names define the custom information to be stored for assets based on their types.
    For example, an asset of type "Computer" could have one property named "MAC Address" and another
    named "Manufacturer."
    """
    __tablename__ = "asset_property_name"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False, index=True)

    asset_type = relationship("AssetType", back_populates="asset_property_names", lazy="raise")
