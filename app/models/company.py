from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    predictions = relationship("PredictionRecord", back_populates="company", cascade="all, delete-orphan")
    actual_returns = relationship("ActualReturnRecord", back_populates="company", cascade="all, delete-orphan")
    recommendations = relationship("RecommendationRecord", back_populates="company", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Company id={self.id} name='{self.name}' email='{self.email}'>"
