"""Base classes for database models"""

from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy import Column, Integer, DateTime

@as_declarative()
class BaseDbModel:
    """Base database model class

    The base model contains columns shared by all tables, for example, the primary key column
    and date/time metadata
    """
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=False)
    modified = Column(DateTime, nullable=True)
