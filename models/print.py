from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from database import Base

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
    client_name = Column(String, nullable=True)
    client_phone = Column(String, nullable=True)
    status = Column(String, default="Pendiente")
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="prints")
    material = relationship("Material", back_populates="prints")