from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from schemas.material import MaterialResponse

class PrintCreate(BaseModel):
    name: str
    material_id: int
    grams_used: float
    print_time_hours: float
    sale_price: float

class PrintResponse(BaseModel):
    id: int
    name: str
    material_id: int
    grams_used: float
    print_time_hours: float
    production_cost: float
    sale_price: float
    profit: float
    is_public: bool
    created_at: datetime
    user_id: int
    material: Optional[MaterialResponse] = None

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_prints: int
    total_sales: float
    total_costs: float
    total_profit: float