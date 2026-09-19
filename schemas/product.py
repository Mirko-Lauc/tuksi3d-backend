from pydantic import BaseModel
from typing import Optional

class ProductBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    grams_required: float
    print_time_hours: float
    suggested_price: float

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    is_public: bool

    class Config:
        from_attributes = True