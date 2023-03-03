"""Module containing Overlay database models"""

from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models import BaseDbModel

MAX_NAME_LENGTH = 100

#==========================================================================================
# Overlay Model
#==========================================================================================
class Overlay(BaseDbModel):
    """Overlay model

    An overlay is an image overlayed on a map. This is typically used to display a
    floor plan, but can be also used to overlay other imagery.

    The overlay must be georeferenced first and the extent boundary must be known.
    """
    __tablename__ = "overlay"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    original_filename = Column(String, nullable=True)
    stored_filename = Column(String, nullable=True)
    extent = Column(
        Geometry(
            geometry_type='POLYGON',
            srid=4326,
            dimension=2
        ),
        nullable=False
    )
    """The bounding box that defines where the overlay is placed on a map"""

    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)
    level = Column(Integer, default=1, nullable=False)

    survey = relationship("Survey", back_populates="overlays", lazy="raise")

    __table_args__ = (
        Index('ix_overlay_survey_id_level', "survey_id", "level"),
    )
