"""Pydantic models for Surveys"""

from datetime import date

from pydantic import BaseModel, Field

from app.database.models.sites import MAX_NAME_LENGTH
from app.schemas._base import BaseSchemaModelInDb

class SurveyBase(BaseModel):
    """Base Pydantic model for a Survey"""
    name: str = Field(max_length=MAX_NAME_LENGTH)
    start_date: date = Field(
        description="The start date, or projected start date, of the survey"
    )
    end_date: date = Field(
        description="The end date, or projected end date, of the survey"
    )
    site_id: int = Field(
        description="The Id of the site this survey is for"
    )
    is_latest: bool = Field(
        description="Indicates if this is the latest survey for this site"
    )

class Survey(SurveyBase, BaseSchemaModelInDb):
    """Pydantic model for a Survey"""

    class Config:
        orm_mode = True

class SurveyCreate(SurveyBase):
    pass

class SurveyUpdate(SurveyBase):
    pass
