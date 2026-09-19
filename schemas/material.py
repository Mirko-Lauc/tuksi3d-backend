from pydantic import BaseModel
from typing import Optional

class MaterialBase(BaseModel):
    name: str
    brand: str
    type: str
    color: str
    cost_per_kg: float
    stock_grams: Optional[float] = 1000.0

class MaterialCreate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: int
    is_public: bool
    user_id: int

    class Config:
        from_attributes = True