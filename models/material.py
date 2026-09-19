from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    brand = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    color = Column(String(50), nullable=False)
    cost_per_kg = Column(Float, nullable=False)
    
    # Campo para saber si es del catálogo base o público
    is_public = Column(Boolean, default=True)
    
    # Relación con el usuario creador (opcional si es base público)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)