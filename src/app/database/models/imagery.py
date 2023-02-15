"""Module containing imagery and related database models"""

from sqlalchemy import Column, String, Integer, Double, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from models.base import BaseModel

class Photo(BaseModel):
    """Photo model

    A photo is a normal photo or a 360 panoramic photo.
    """
    __tablename__ = "photo"

    name = Column(String(length=100), nullable=False)
    description = Column(String(length=255), nullable=True)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    # direction relative to true north the camera was facing (center of the image)
    heading = Column(Double, nullable=False, default=0.0)
    # If None (the default), then the photo is a normal photo (not a pano). If False, the photo is a
    # single file, spherical pano. If True, the pano is a 6 file cubic.
    is_cubic_pano = Column(Boolean, nullable=True, default=None)
    # If this is a cubic pano, then the filename should be a prefix or template.
    # Filenames are nullable to allow for disconnected data collection, i.e. the images have not been pulled
    # from the camera yet, but they have been placed on the map.
    original_filename = Column(String(length=255), nullable=True)
    stored_filename = Column(String(length=255), nullable=True)
    # a custom marker makes it easy to track the record with the actual image file for disconnected
    # data collection
    custom_marker = Column(String(length=100), nullable=True)
    floor_id = Column(Integer, ForeignKey("floor.id"), nullable=False, index=True)

    floor = relationship("Floor", back_populates="photos")
    # The hotspots visible in this photo
    hotspots = relationship("Hotspot", back_populates="source_photo")
    # The hotspots that have this photo as the destination photo
    source_hotspots = relationship("Hotspots", back_populates="destination_photo")

class Hotspot(BaseModel):
    """Hotspot model

    A hotspot is an item tagged in a photo, usually visualized by an icon. The item can be an
    asset or another photo.

    Asset hotspots easily allow a user to get an asset's information from within the
    photo/panoramic viewer.

    Photo Hotspots allow a user to visually traverse from one photo to another. Typically, they are used
    to traverse between panos, like the arrow icons in Google Maps street view.
    """
    __tablename__ = "hotspot"

    source_photo_id = Column(Integer, ForeignKey("photo.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=True, index=True)
    destination_photo_id = Column(Integer, ForeignKey("photo.id"), nullable=True, index=True)

    # the x and y coordinate specify the location of the hotspot in the source photo.
    # The values will differ depending on the source photo type:
    # For a pano, x and y are in the range [-pi, pi] with the origin at the center of the image.
    # For a normal photo, x and y are in the range [0, 1] with the origin at the top left of the image.
    # NOTE: if we had 3 dimensional data for all assets and photos, these values could be determined automatically
    x_coord = Column(Double, nullable=False)
    y_coord = Column(Double, nullable=False)

    source_photo = relationship("Photo", back_populates="hotspots")
    asset = relationship("Asset", back_populates="asset_hotspots")
    destination_photo = relationship("Photo", "source_hotspots")

    def is_asset_hotspot(self) -> bool:
        return self.asset_id is not None

    def is_photo_hotspot(self) -> bool:
        return self.destination_photo_id is not None
