from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from app.db.database import Base

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    target_generation = Column(String, nullable=True) 

    campaigns = relationship("Campaign", back_populates="product")


class Audience(Base):
    __tablename__ = 'audiences'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    segment_size = Column(Integer, nullable=False)
    description = Column(String, nullable=True)

    campaigns = relationship("Campaign", back_populates="audience")


class Campaign(Base):
    __tablename__ = 'campaigns'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    budget = Column(Float, nullable=False)
    
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    audience_id = Column(Integer, ForeignKey('audiences.id', ondelete='CASCADE'), nullable=False)

    product = relationship("Product", back_populates="campaigns")
    audience = relationship("Audience", back_populates="campaigns")
    metrics = relationship("PerformanceMetric", back_populates="campaign")

class PerformanceMetric(Base):
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('campaigns.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)

    campaign = relationship("Campaign", back_populates="metrics")