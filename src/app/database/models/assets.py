"""Module containing asset and related database models"""

from sqlalchemy import Column, String, Integer, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from _base import BaseModel

class Asset(BaseModel):
    """Asset model

    An asset is an item of interest which occupies a phyiscal point in space
    """
    __tablename__ = "asset"

    name = Column(String(length=100), nullable=False)
    description = Column(String(length=255), nullable=True)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False, index=True)
    floor_id = Column(Integer, ForeignKey("floor.id"), nullable=False, index=True)

    asset_type = relationship("AssetType", back_populates="assets")
    asset_properties = relationship("AssetProperty", back_populates="asset")
    floor = relationship("Floor", back_populates="assets")
    asset_hotspots = relationship("Hotspot", back_populates="asset")

class AssetType(BaseModel):
    """Asset Type model

    Asset types help distinguish assets from each other
    """
    __tablename__ = "asset"

    name = Column(String(length=100), nullable=False)
    description = Column(String(length=255), nullable=True)
    category = Column(String(length=100), nullable=True)
    # TODO: Constrain the icon size somewhere else
    icon = Column(LargeBinary, nullable=False)

    assets = relationship("Asset", back_populates="asset_type")
    asset_property_names = relationship("AssetPropertyName", back_populates="asset_type")

class AssetPropertyName(BaseModel):
    """Asset Property Name model

    Asset property names define the custom information to be stored for assets based on their types.
    For example, an asset of type "Computer" could have one property named "MAC Address" and another
    named "Manufacturer."
    """
    __tablename__ = "asset_property_name"

    name = Column(String(length=100), nullable=False)
    asset_type_id = Column(Integer, ForeignKey("asset_type.id"), nullable=False, index=True)
    #TODO: Figure out how to store allowed values (a dropdown)
    #allowed_values =

    asset_type = relationship("AssetType", back_populates="asset_property_names")
    asset_properties = relationship("AssetProperty", back_populates="asset_property_name")

class AssetProperty(BaseModel):
    """Asset Property model

    Asset properties are the actual, custom information stored for assets.
    """
    __tablename__ = "asset_property"

    value = Column(String, nullable=False)
    # NOTE: By only using a foreign key to get the property name, rather than storing the name again here,
    # an asset's properties can "change" when the property name changes. This may or may not be desired behavior.
    asset_property_name_id = Column(Integer, ForeignKey("asset_property_name.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=False, index=True)

    asset_property_name = relationship("AssetPropertyName", back_populates="asset_properties")
    asset = relationship("Asset", back_populates="asset_properties")
