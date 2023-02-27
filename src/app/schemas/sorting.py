"""Pydantic models for sorting API query results"""

from enum import Enum

class SortBy(str, Enum):
    ID = "id"
    CREATED = "created"
    MODIFIED = "modified"

class SortByWithName(SortBy):
    NAME = "name"

class SortDirection(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"
