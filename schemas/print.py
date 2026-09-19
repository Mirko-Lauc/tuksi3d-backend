from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from schemas.material import MaterialResponse


class PrintCreate(BaseModel):
    name: str = Field(..., description="Nombre del trabajo o pieza (ej: Soporte Auriculares)")
    material_id: int = Field(..., description="ID del material/filamento utilizado")
    grams_used: float = Field(..., gt=0, description="Peso de la pieza en gramos")
    print_time_hours: float = Field(..., gt=0, description="Tiempo de impresión en horas")
    sale_price: float = Field(..., gt=0, description="Precio final de venta cobrado al cliente")


class PrintResponse(BaseModel):
    id: int
    name: str
    material_id: int
    grams_used: float
    print_time_hours: float
    production_cost: float
    sale_price: float
    profit: float
    created_at: datetime
    material: Optional[MaterialResponse] = None

    class Config:
        from_attributes = True
        