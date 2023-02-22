"""Pydantic models for Sites and related models"""

import math
from datetime import date

from pydantic import Field

from database.models.sites import MAX_NAME_LENGTH
from app.schemas._base import BaseSchemaModelInDb

class Site(BaseSchemaModelInDb):
    """Pydantic model for a Site"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    latitude: float = Field(ge=-math.pi/2, le=math.pi/2)
    longitude: float = Field(ge=-math.pi, le=math.pi)
    parent_site_id: int | None = None

class Survey(BaseSchemaModelInDb):
    """Pydantic model for a Survey"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    start_date: date
    end_date: date
    site_id: int
    is_latest: bool = False
