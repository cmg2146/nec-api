"""Base classes for database models"""

from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase

class BaseDbModel(DeclarativeBase):
    """Base database model class

    The base model contains columns shared by all tables, for example, the primary key column
    and date/time metadata
    """
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, nullable=False)
    modified = Column(DateTime, nullable=True)
