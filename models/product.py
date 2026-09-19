from sqlalchemy import Column, Integer, String, Float, Boolean
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    grams_required = Column(Float, nullable=False)
    print_time_hours = Column(Float, nullable=False)
    suggested_price = Column(Float, nullable=False)
    is_public = Column(Boolean, default=True)