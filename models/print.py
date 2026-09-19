from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class PrintJob(Base):
    __tablename__ = "prints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    grams_used = Column(Float, nullable=False)
    print_time_hours = Column(Float, nullable=False)
    production_cost = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=False)
    profit = Column(Float, nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    material = relationship("Material")
    user = relationship("User")