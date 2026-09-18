from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    brand = Column(String(100), nullable=True)
    type = Column(String(50), nullable=False)
    color = Column(String(50), nullable=True)
    cost_per_kg = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)