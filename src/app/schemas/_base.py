"""Base classes used by all Pydantic schema models"""

from datetime import datetime

from pydantic import BaseModel, Field

class BaseSchemaModelInDb(BaseModel):
    id: int = Field(example=1)
    created: datetime = Field(
        description="The UTC date and time this record was created"
    )
    modified: datetime | None = Field(
        default=None,
        description="The UTC date and time this record was last modified"
    )
