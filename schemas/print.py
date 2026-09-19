from pydantic import BaseModel
import datetime
from typing import Optional
from schemas.material import MaterialResponse

class PrintBase(BaseModel):
    name: str
    material_id: int
    grams_used: float
    print_time_hours: float
    sale_price: float
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    status: Optional[str] = "Pendiente"

class PrintCreate(PrintBase):
    pass

class PrintResponse(PrintBase):
    id: int
    production_cost: float
    profit: float
    is_public: bool
    created_at: datetime.datetime
    user_id: int
    material: Optional[MaterialResponse] = None

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_prints: int
    total_sales: float
    total_costs: float
    total_profit: float