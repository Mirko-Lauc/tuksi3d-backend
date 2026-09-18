from pydantic import BaseModel, Field


class CostCalculationInput(BaseModel):
    # Datos de la pieza
    grams_used: float = Field(
        ..., gt=0, description="Peso de la pieza en gramos"
    )
    print_time_hours: float = Field(
        ..., gt=0, description="Tiempo de impresión en horas"
    )

    # Datos del insumo y máquina
    filament_cost_per_kg: float = Field(
        25000.0, gt=0, description="Precio del kg de filamento en ARS"
    )
    printer_power_watts: float = Field(
        150.0, gt=0, description="Consumo promedio de la impresora en Watts"
    )
    electricity_kwh_rate: float = Field(
        120.0, gt=0, description="Costo del kWh en ARS"
    )

    # Margenes configurables
    waste_percentage: float = Field(
        5.0,
        ge=0,
        description="Porcentaje de error/desperdicio (ej: 5.0 para 5%)",
    )
    machine_depreciation_percentage: float = Field(
        10.0, ge=0, description="Porcentaje de desgaste/mantenimiento de máquina"
    )

    # Multiplicadores de venta
    retail_multiplier: float = Field(
        4.0, gt=0, description="Multiplicador minorista (ej: x4)"
    )
    wholesale_multiplier: float = Field(
        3.0, gt=0, description="Multiplicador mayorista (ej: x3)"
    )
    small_item_multiplier: float = Field(
        5.0, gt=0, description="Multiplicador para llaveros/piezas chicas (ej: x5)"
    )


class CostCalculationOutput(BaseModel):
    # Desglose de costos directos
    filament_cost: float
    electricity_cost: float
    waste_cost: float
    depreciation_cost: float
    total_production_cost: float

    # Precios de venta sugeridos
    retail_price: float
    wholesale_price: float
    small_item_price: float

    # Ganancias estimadas
    retail_profit: float
    wholesale_profit: float
    small_item_profit: float