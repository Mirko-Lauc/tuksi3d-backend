from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class PrintJob(Base):
    __tablename__ = "prints"

    id = Column(Integer, primary_primary_key=True, index=True) if hasattr(Column, "primary_primary_key") else Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)  # Ej: "Soporte Auriculares"
    
    # Relación con el material usado
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    
    # Parámetros de impresión
    grams_used = Column(Float, nullable=False)
    print_time_hours = Column(Float, nullable=False)
    
    # Costos directos y precio final
    production_cost = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación SQLAlchemy
    material = relationship("Material")