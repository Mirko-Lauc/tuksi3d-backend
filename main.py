from fastapi import FastAPI
from schemas.cost import CostCalculationInput, CostCalculationOutput

app = FastAPI(
    title="Tuksi 3D API",
    description="Backend para gestión y cálculo de costos de Tuksi 3D",
    version="1.0.0",
)


@app.get("/")
def read_root():
    return {"status": "online", "system": "Tuksi 3D Cost Engine"}


@app.post("/calculate-cost", response_model=CostCalculationOutput)
def calculate_cost(data: CostCalculationInput):
    # 1. Costo base de filamento (con desperdicio)
    cost_per_gram = data.filament_cost_per_kg / 1000.0
    base_filament_cost = data.grams_used * cost_per_gram
    waste_cost = base_filament_cost * (data.waste_percentage / 100.0)
    total_filament_cost = base_filament_cost + waste_cost

    # 2. Costo de electricidad (Watts -> kW * Horas * Tarifa)
    kw_consumed = (data.printer_power_watts / 1000.0) * data.print_time_hours
    electricity_cost = kw_consumed * data.electricity_kwh_rate

    # 3. Desgaste / Mantenimiento de máquina
    subtotal_direct_cost = total_filament_cost + electricity_cost
    depreciation_cost = subtotal_direct_cost * (
        data.machine_depreciation_percentage / 100.0
    )

    # 4. Costo Total de Producción Real
    total_cost = subtotal_direct_cost + depreciation_cost

    # 5. Precios de Venta
    retail_price = total_cost * data.retail_multiplier
    wholesale_price = total_cost * data.wholesale_multiplier
    small_item_price = total_cost * data.small_item_multiplier

    return CostCalculationOutput(
        filament_cost=round(base_filament_cost, 2),
        electricity_cost=round(electricity_cost, 2),
        waste_cost=round(waste_cost, 2),
        depreciation_cost=round(depreciation_cost, 2),
        total_production_cost=round(total_cost, 2),
        retail_price=round(retail_price, 2),
        wholesale_price=round(wholesale_price, 2),
        small_item_price=round(small_item_price, 2),
        retail_profit=round(retail_price - total_cost, 2),
        wholesale_profit=round(wholesale_price - total_cost, 2),
        small_item_profit=round(small_item_price - total_cost, 2),
    )