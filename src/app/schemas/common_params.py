"""Common classes for API endpoints"""

from enum import Enum

from fastapi import Query

class SortBy(str, Enum):
    ID = "id"
    CREATED = "created"
    MODIFIED = "modified"
    NAME = "name"

class CommonQueryParams:
    """Common query parameters used by GET endpoints returning collections"""
    def __init__(
        self,
        sort_by: SortBy = Query(
            default=SortBy.ID,
            description="The field to sort results by"
        ),
        sort_desc: bool = Query(
            default=False,
            description="True - sort high to low, False - sort low to high (default)"
        ),
        skip: int | None = Query(
            default=None,
            ge=0,
            description="Skip the specified number of items (for pagination)"
        ),
        limit: int | None = Query(
            default=None,
            ge=1,
            description="Max number of results to get"
        )
    ):
        self.sort_by = sort_by
        self.sort_desc = sort_desc
        self.skip = skip
        self.limit = limit
