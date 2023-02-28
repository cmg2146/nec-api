"""Module containing high-level database models for sites and surveys"""

from sqlalchemy import Column, String, DateTime, Date, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

from app.database.models import BaseDbModel

MAX_NAME_LENGTH = 100

class Site(BaseDbModel):
    """Site model

    A site is a physical location or facility. A site can contain sub-sites and each site
    and sub-site can contain one or more surveys.
    """
    __tablename__ = "site"

    name = Column(String(length=MAX_NAME_LENGTH), nullable=False)
    coordinates = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False)
    """The latitude and longitude of the site."""

    parent_site_id = Column(Integer, ForeignKey("site.id"), nullable=True, index=True)

    surveys = relationship("Survey", back_populates="site", lazy="raise")
    sub_sites = relationship("Site", lazy="raise")

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
    overlays = relationship("Overlay", back_populates="survey", lazy="raise")
    assets = relationship("Asset", back_populates="survey", lazy="raise")
    panos = relationship("Pano", back_populates="survey", lazy="raise")
    photos = relationship("Photo", back_populates="survey", lazy="raise")

    __table_args__ = (
        # There should only be one "latest" survey per site
        UniqueConstraint("site_id", "is_latest"),
    )
