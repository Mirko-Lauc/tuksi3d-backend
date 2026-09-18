from pydantic import BaseModel
from typing import Optional

class MaterialCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    type: str
    color: Optional[str] = None
    cost_per_kg: float

class MaterialResponse(MaterialCreate):
    id: int

    class Config:
        from_attributes = True