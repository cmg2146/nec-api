"""Module containing photo and related database models"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models import BaseDbModel

MAX_NAME_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 255

#==========================================================================================
# Photo Model
#==========================================================================================
class Photo(BaseDbModel):
    """Photo model"""
    __tablename__ = "photo"

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
    """The latitude and longitude of the photo."""

    heading = Column(Float, nullable=True, default=None)
    """Direction, relative to true north, of the center of the photo.

    If None, the heading is unknown or unset.
    """

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
    """Custom data to associate a photo record with the correct image file.

    The custom marker is useful when the actual photos do not get uploaded until after
    data has been collected. The marker allows the file to be tracked with the database
    record and also allows photos to be bulk uploaded.
    """

    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    level = Column(Integer, default=1, nullable=False)

    survey = relationship(
        "Survey",
        back_populates="photos",
        lazy="raise"
    )

    __table_args__ = (
        Index('ix_photo_survey_id_level', "survey_id", "level"),
    )
