from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_identifier = Column(String(100), nullable=False, index=True)  # SKU / Catalog ID
    product_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False, index=True)
    sub_category = Column(String(100), nullable=False, index=True)
    brand = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "product_identifier", name="uq_company_product_sku"),
    )

    # Relationships
    company = relationship("Company", back_populates="products")
    predictions = relationship("PredictionRecord", back_populates="product")
    actual_returns = relationship("ActualReturnRecord", back_populates="product")
    recommendations = relationship("RecommendationRecord", back_populates="product")

    def __repr__(self):
        return f"<Product id={self.id} sku='{self.product_identifier}' company_id={self.company_id}>"
