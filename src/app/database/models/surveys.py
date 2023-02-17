"""Module containing high-level data collection database models"""

from sqlalchemy import Column, String, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from _base import BaseModel

class Site(BaseModel):
    """Site model

    A site is a physical location containing one or more surveys
    """
    __tablename__ = "site"

    name = Column(String(length=100), nullable=False)
    # NOTE: A site will comprise a large geographic area - point coordinates are used to locate the site easily
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)

    surveys = relationship("Survey", back_populates="site")

class Survey(BaseModel):
    """Survey model

    A survey is a data collection visit to a site.
    """
    __tablename__ = "survey"

    name = Column(String(length=100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False, index=True)
    is_latest = Column(Boolean, nullable=False, default=False)

    site = relationship("Site", back_populates="surveys")
    sub_surveys = relationship("SubSurvey", back_populates="survey")
    floors = relationship("Floor", back_populates="survey")

    # There should only be one "latest" survey per site
    UniqueConstraint("site_id", "is_latest")

class SubSurvey(BaseModel):
    """Sub Survey model

    A sub survey is a part of the complete site survey. A sub survey could be useful for large sites,
    for example, a sub survey of "Building 25" and another for "Building 40." Sub-surveys are not
    required for a survey.
    """
    __tablename__ = "sub_survey"

    name = Column(String(length=100), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)

    survey = relationship("Survey", back_populates="sub_surveys")
    floors = relationship("Floor", back_populates="sub_survey")

class Floor(BaseModel):
    """Floor model

    Many surveyed sites have buildings and many buildings have multiple floors, thus, the need
    for a Floor model. Consequently, all collected data will be associated with a floor from the
    survey (or sub-survey).

    A floor record must be created even for sites surveyed without multiple floors. For such a
    survey, a floor named "First Level" or "Ground Level" can be used.
    """
    __tablename__ = "floor"

    name = Column(String(length=100), nullable=False)
    # By making both nullable, we leave it up to the users to decide if a floor should point
    # to both the survey and sub-survey (if sub-surveys are in use).
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=True, index=True)
    sub_survey_id = Column(Integer, ForeignKey("sub_survey.id"), nullable=True, index=True)

    survey = relationship("Survey", back_populates="floors")
    sub_survey = relationship("SubSurvey", back_populates="floors")
    floor_overlays = relationship("FloorOverlay", back_populates="floor")
    assets = relationship("Asset", back_populates="floor")
    photos = relationship("Photo", back_populates="floor")

class FloorOverlay(BaseModel):
    """Floor Overlay model

    A floor overlay is an image overlayed on a floor. This is typically used to display a
    floor plan for each floor in the survey, but can be also used to overlay other imagery.

    The overlay must be georeferenced first and the extent boundary must be known.
    """
    __tablename__ = "floor_overlay"

    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    extent = Column(Geometry(geometry_type='POLYGON', srid=4326, dimension=2), nullable=False)
    floor_id = Column(Integer, ForeignKey("floor.id"), nullable=False, index=True)

    floor = relationship("Floor", back_populates="floor_overlays")
