from datetime import datetime

from pydantic import BaseModel


class OrganizationRead(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True