"""Module containing photo and related database models"""

from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models import BaseDbModel

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 255

#==========================================================================================
# Pano Model
#==========================================================================================
class Pano(BaseDbModel):
    """Pano model

    A pano is a 360 degree, panoramic photo.
    """
    __tablename__ = "pano"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    description = Column(String(length=MAX_DESCRIPTION_LENGTH), nullable=True)
    coordinates = Column(
        Geometry(
            geometry_type='POINT',
            srid=4326,
            spatial_index=True
        ),
        nullable=False
    )
    """The latitude and longitude of the pano."""

    heading = Column(Float, nullable=True, default=None)
    """Direction, relative to true north, of the center of the pano."""

    is_cubic_pano = Column(Boolean, nullable=False, default=False)
    """Indicates if this is a cubic instead of spherical pano."""

    original_filename = Column(String(length=255), nullable=True)
    """Original or uploaded filename.

    Column is nullable to allow for disconnected data collection, i.e. photos have not
    been pulled from the camera yet, but they have been placed on the map.
    """

    stored_filename = Column(String(length=255), nullable=True)
    """Filename stored on disk.

    The file name stored on disk will be different from the original/uploaded file name.

    Column is nullable to allow for disconnected data collection, i.e. photos have not
    been pulled from the camera yet, but they have been placed on the map.
    """

    custom_marker = Column(String(length=MAX_NAME_LENGTH), nullable=True)
    """Custom data to associate a pano record with the correct image file.

    The custom marker is useful when the actual photos do not get uploaded until after
    data has been collected. The marker allows the file to be tracked with the database
    record and also allows photos to be bulk uploaded.
    """

    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    level = Column(Integer, default=1, nullable=False)

    survey = relationship(
        "Survey",
        back_populates="panos",
        lazy="raise"
    )
    hotspots = relationship(
        "Hotspot",
        foreign_keys="Hotspot.pano_id",
        back_populates="pano",
        lazy="raise"
    )
    """The hotspots visible in this pano."""

    source_hotspots = relationship(
        "Hotspot",
        foreign_keys="Hotspot.destination_pano_id",
        back_populates="destination_pano",
        lazy="raise"
    )
    """The hotspots that have this pano as the destination pano."""

    __table_args__ = (
        Index('ix_pano_survey_id_level', "survey_id", "level"),
    )

#==========================================================================================
# Hotspot Model
#==========================================================================================
class Hotspot(BaseDbModel):
    """Hotspot model

    A hotspot is an item tagged in a pano, usually visualized by an icon. The item can be an
    asset or another pano.

    Asset hotspots easily allow a user to get an asset's information from within the
    pano viewer.

    Pano hotspots, or pano links, allow a user to visually traverse from one pano to another,
    like the arrow icons in Google Maps street view.
    """
    __tablename__ = "hotspot"

    pano_id = Column(Integer, ForeignKey("pano.id"), nullable=False, index=True)
    """The ID of the pano this hotspot is visible in."""

    asset_id = Column(Integer, ForeignKey("asset.id"), nullable=True, index=True)
    """The ID of the asset this hotspot references."""

    destination_pano_id = Column(Integer, ForeignKey("pano.id"), nullable=True, index=True)
    """The ID of the pano this hotspot links to."""

    # NOTE: if we had 3 dimensional data for all assets and panos (and image processing),
    # hotspots could be located automatically.
    yaw = Column(Float, nullable=False)
    """Horizontal location of the hotspot in the pano.

    The value is in the range [-180, 180] with the origin at the center of the image.
    """

    pitch = Column(Float, nullable=False)
    """Vertical location of the hotspot in the pano.

    The value is in the range [-90, 90] with the origin at the center of the image.
    """

    pano = relationship(
        "Pano",
        foreign_keys=[pano_id],
        back_populates="hotspots",
        lazy="raise"
    )
    asset = relationship(
        "Asset",
        back_populates="asset_hotspots",
        lazy="raise"
    )
    destination_pano = relationship(
        "Pano",
        foreign_keys=[destination_pano_id],
        back_populates="source_hotspots",
        lazy="raise"
    )

    def is_asset_hotspot(self) -> bool:
        return self.asset_id is not None

    def is_pano_hotspot(self) -> bool:
        return self.destination_pano_id is not None
