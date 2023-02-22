"""Base classes used by all models de"""

from datetime import datetime

from pydantic import BaseModel

class BaseSchemaModel(BaseModel):
    created: datetime = datetime.utcnow
    modified: datetime | None = None

class BaseSchemaModelInDb(BaseSchemaModel):
    id: int
