from pydantic import BaseModel
from typing import Optional


class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0

    class Config:
        from_attributes = True
