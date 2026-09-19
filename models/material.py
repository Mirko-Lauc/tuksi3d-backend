from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Material(Base):
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    type = Column(String, nullable=False)
    color = Column(String, nullable=False)
    cost_per_kg = Column(Float, nullable=False)
    stock_grams = Column(Float, default=1000.0)
    is_public = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="materials")
    prints = relationship("PrintJob", back_populates="material")