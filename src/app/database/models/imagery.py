"""Module containing imagery and related database models"""

from sqlalchemy import Column, String, Integer, Double, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models._base import BaseDbModel

class Photo(BaseDbModel):
    """Photo model

    A photo is a normal photo or a 360 panoramic photo.
    """
    __tablename__ = "photo"

    name = Column(String(length=100), nullable=False)
    description = Column(String(length=255), nullable=True)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    """The latitude and longitude of the photo."""

    heading = Column(Double, nullable=False, default=0.0)
    """Direction, relative to true north, of the center of the photo."""

    is_cubic_pano = Column(Boolean, nullable=True, default=None)
    """Indicates the type of photo.

    None (the default) - normal photo (not a 360 degree pano).

    False - 360 degree, single file, spherical pano.

    True - 360 degree, six file, cubic pano.
    """

    original_filename = Column(String(length=255), nullable=True)
    """Original or uploaded filename.

    Column is nullable to allow for disconnected data collection, i.e. photos have not been pulled
    from the camera yet, but they have been placed on the map.
    """

    stored_filename = Column(String(length=255), nullable=True)
    """Filename stored on disk.

    The file name stored on disk will be different from the original/uploaded file name.

    Column is nullable to allow for disconnected data collection, i.e. photos have not been pulled
    from the camera yet, but they have been placed on the map.
    """

    custom_marker = Column(String(length=100), nullable=True)
    """Custom data to associate a photo record with the correct image file.

    The custom marker is useful when the actual photos do not get uploaded until after data
    has been collected. The marker allows the file to be tracked with the database record and
    also allows photos to be bulk uploaded.
    """

    floor_id = Column(Integer, ForeignKey("floor.id"), nullable=False, index=True)

    floor = relationship("Floor", back_populates="photos")
    hotspots = relationship("Hotspot", back_populates="source_photo")
    """The hotspots visible in this photo."""

    source_hotspots = relationship("Hotspots", back_populates="destination_photo")
    """The hotspots that have this photo as the destination photo."""

class Hotspot(BaseDbModel):
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
    """The ID of the photo this hotspot is visible in."""

    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=True, index=True)
    """The ID of the asset this hotspot references, if this is an asset hotspot."""

    destination_photo_id = Column(Integer, ForeignKey("photo.id"), nullable=True, index=True)
    """The ID of the photo this hotspot references, if this is a photo hotspot."""

    # NOTE: if we had 3 dimensional data for all assets and photos (and image processing), hotspots could
    # be located automatically.
    x_coord = Column(Double, nullable=False)
    """Horizontal location of the hotspot in the photo.

    For a pano, the value is in the range [-pi, pi] with the origin at the center of the image.

    For a normal photo, the value is in the range [0, 1] with the origin at the top left of the image.
    """

    y_coord = Column(Double, nullable=False)
    """Vertical location of the hotspot in the photo.

    For a pano, the value is in the range [-pi/2, pi/2] with the origin at the center of the image.

    For a normal photo, the value is in the range [0, 1] with the origin at the top left of the image.
    """

    source_photo = relationship("Photo", back_populates="hotspots")
    asset = relationship("Asset", back_populates="asset_hotspots")
    destination_photo = relationship("Photo", "source_hotspots")

    def is_asset_hotspot(self) -> bool:
        return self.asset_id is not None

    def is_photo_hotspot(self) -> bool:
        return self.destination_photo_id is not None
