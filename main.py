from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from database import engine, Base, get_db
import models.material
import models.print
from models.material import Material
from models.print import PrintJob
from schemas.cost import CostCalculationInput, CostCalculationOutput
from schemas.material import MaterialCreate, MaterialResponse
from schemas.print import PrintCreate, PrintResponse

app = FastAPI(
    title="Tuksi 3D - API",
    description="Backend de gestión y cálculo de costos para impresión 3D",
    version="1.0.0"
)

# Permitir peticiones desde cualquier origen (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Evento de inicio: crea las tablas en PostgreSQL si no existen
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- Endpoint de Cálculo de Costos ---
@app.post("/calculate-cost", response_model=CostCalculationOutput)
async def calculate_cost(
    data: CostCalculationInput,
    db: AsyncSession = Depends(get_db)
):
    cost_per_kg = data.filament_cost_per_kg

    if data.material_id:
        result = await db.execute(select(Material).where(Material.id == data.material_id))
        material = result.scalar_one_or_none()
        if not material:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Material con ID {data.material_id} no encontrado"
            )
        cost_per_kg = material.cost_per_kg

    if cost_per_kg is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Debes ingresar un 'material_id' o especificar 'filament_cost_per_kg'"
        )

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

# --- Endpoints de Materiales ---
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

# --- Endpoints de Trabajos de Impresión (`prints`) ---
@app.post("/prints", response_model=PrintResponse, status_code=status.HTTP_201_CREATED)
async def create_print_job(
    print_data: PrintCreate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Material).where(Material.id == print_data.material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material con ID {print_data.material_id} no encontrado"
        )

    filament_cost = (print_data.grams_used / 1000.0) * material.cost_per_kg
    electricity_cost = ((350.0 / 1000.0) * print_data.print_time_hours) * 120.0
    waste_cost = filament_cost * 0.05
    depreciation_cost = (filament_cost + electricity_cost) * 0.10
    
    prod_cost = round(filament_cost + electricity_cost + waste_cost + depreciation_cost, 2)
    profit = round(print_data.sale_price - prod_cost, 2)

    new_print = PrintJob(
        name=print_data.name,
        material_id=print_data.material_id,
        grams_used=print_data.grams_used,
        print_time_hours=print_data.print_time_hours,
        production_cost=prod_cost,
        sale_price=print_data.sale_price,
        profit=profit
    )

    db.add(new_print)
    await db.commit()
    await db.refresh(new_print)
    
    result_loaded = await db.execute(
        select(PrintJob).options(selectinload(PrintJob.material)).where(PrintJob.id == new_print.id)
    )
    return result_loaded.scalar_one()

@app.get("/prints", response_model=List[PrintResponse])
async def list_print_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PrintJob).options(selectinload(PrintJob.material)))
    return result.scalars().all()