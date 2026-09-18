from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import engine, Base, get_db
import models.material
from models.material import Material
from schemas.cost import CostCalculationInput, CostCalculationOutput
from schemas.material import MaterialCreate, MaterialResponse

app = FastAPI(
    title="Tuksi 3D - API",
    description="Backend de gestión y cálculo de costos para impresión 3D",
    version="1.0.0"
)

# Evento de inicio: crea las tablas en PostgreSQL si no existen
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Endpoint de Cálculo de Costos (Conectado a DB) ---
@app.post("/calculate-cost", response_model=CostCalculationOutput)
async def calculate_cost(
    data: CostCalculationInput,
    db: AsyncSession = Depends(get_db)
):
    cost_per_kg = data.filament_cost_per_kg

    # Si se envía un material_id, se busca el costo en la base de datos
    if data.material_id:
        result = await db.execute(select(Material).where(Material.id == data.material_id))
        material = result.scalar_one_or_none()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Material con ID {data.material_id} no encontrado"
            )
        cost_per_kg = material.cost_per_kg

    # Validación si no se ingresó ni material_id ni costo manual
    if cost_per_kg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Debes ingresar un 'material_id' o especificar 'filament_cost_per_kg'"
        )

    # Cálculos
    filament_cost = (data.grams_used / 1000.0) * cost_per_kg
    kwh_used = (data.printer_power_watts / 1000.0) * data.print_time_hours
    electricity_cost = kwh_used * data.electricity_kwh_rate
    waste_cost = filament_cost * (data.waste_percentage / 100.0)
    depreciation_cost = (filament_cost + electricity_cost) * (data.machine_depreciation_percentage / 100.0)

    total_production_cost = filament_cost + electricity_cost + waste_cost + depreciation_cost

    retail_price = total_production_cost * data.retail_multiplier
    wholesale_price = total_production_cost * data.wholesale_multiplier
    small_item_price = total_production_cost * data.small_item_multiplier

    return CostCalculationOutput(
        filament_cost=round(filament_cost, 2),
        electricity_cost=round(electricity_cost, 2),
        waste_cost=round(waste_cost, 2),
        depreciation_cost=round(depreciation_cost, 2),
        total_production_cost=round(total_production_cost, 2),
        retail_price=round(retail_price, 2),
        wholesale_price=round(wholesale_price, 2),
        small_item_price=round(small_item_price, 2),
        retail_profit=round(retail_price - total_production_cost, 2),
        wholesale_profit=round(wholesale_price - total_production_cost, 2),
        small_item_profit=round(small_item_price - total_production_cost, 2)
    )

# --- Endpoints de Gestión de Materiales (CRUD) ---
@app.post("/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def create_material(
    material: MaterialCreate,
    db: AsyncSession = Depends(get_db)
):
    new_material = Material(
        name=material.name,
        brand=material.brand,
        type=material.type,
        color=material.color,
        cost_per_kg=material.cost_per_kg
    )
    db.add(new_material)
    await db.commit()
    await db.refresh(new_material)
    return new_material

@app.get("/materials", response_model=List[MaterialResponse])
async def list_materials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Material))
    return result.scalars().all()