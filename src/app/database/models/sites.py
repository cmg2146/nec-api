"""Module containing high-level data collection database models"""

from sqlalchemy import Column, String, DateTime, Date, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models._base import BaseDbModel

MAX_NAME_LENGTH = 100

class Site(BaseDbModel):
    """Site model

    A site is a physical location or facility. A site can contain sub-sites and each site
    and sub-site can contain one or more surveys.
    """
    __tablename__ = "site"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    """The latitude and longitude of the site."""

    parent_site_id = Column(Integer, ForeignKey("site.id"), nullable=True, index=True)

    surveys = relationship("Survey", back_populates="site", lazy="raise")
    parent_site = relationship("Site", back_populates="sub_sites", lazy="raise")
    sub_sites = relationship("Site", back_populates="parent_site", lazy="raise")

class Survey(BaseDbModel):
    """Survey model

    A survey is a data collection visit to a site.
    """
    __tablename__ = "survey"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False, index=True)
    is_latest = Column(Boolean, nullable=False, default=False)

    site = relationship("Site", back_populates="surveys", lazy="raise")
    floors = relationship("Floor", back_populates="survey", lazy="raise")

    # There should only be one "latest" survey per site
    UniqueConstraint("site_id", "is_latest")

class Floor(BaseDbModel):
    """Floor model

    Many surveyed sites have buildings and many buildings have multiple floors, thus, the need
    for a Floor model. Consequently, all collected data will be associated with a floor from the
    survey.

    A floor record must be created even for sites surveyed without multiple floors. For such a
    survey, a floor named "First Level" or "Ground Level" can be used.
    """
    __tablename__ = "floor"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    survey_id = Column(Integer, ForeignKey("survey.id"), nullable=False, index=True)

    survey = relationship("Survey", back_populates="floors", lazy="raise")
    floor_overlays = relationship("FloorOverlay", back_populates="floor", lazy="raise")
    assets = relationship("Asset", back_populates="floor", lazy="raise")
    photos = relationship("Photo", back_populates="floor", lazy="raise")

class FloorOverlay(BaseDbModel):
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

    floor = relationship("Floor", back_populates="floor_overlays", lazy="raise")
