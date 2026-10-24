from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class ActualReturnRecord(Base):
    __tablename__ = "actual_return_records"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)

    # Identifiers
    order_reference = Column(String(100), nullable=True, index=True)
    product_identifier = Column(String(100), nullable=True, index=True)  # SKU / Model ID

    # Order and Catalog Attributes
    product_category = Column(String(100), nullable=False, index=True)
    sub_category = Column(String(100), nullable=True, index=True)
    brand = Column(String(100), nullable=True, index=True)
    product_price = Column(Float, nullable=True)
    discount_percent = Column(Float, nullable=True)
    fulfillment_type = Column(String(100), nullable=True)
    payment_method = Column(String(100), nullable=True)
    quantity = Column(Integer, default=1, nullable=False)
    defect_rate = Column(Float, nullable=True)

    # Outcome tracking (point-in-time separated)
    order_date = Column(Date, nullable=False, index=True)
    return_date = Column(Date, nullable=True)
    was_returned = Column(Integer, nullable=True, index=True)  # 1 = returned, 0 = kept, None = unknown/pending
    return_reason = Column(String(255), nullable=True, index=True)
    return_status = Column(String(50), default="completed", nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "order_reference", name="uq_company_order_reference"),
    )

    # Relationships
    company = relationship("Company", back_populates="actual_returns")
    product = relationship("Product", back_populates="actual_returns")

    def __repr__(self):
        return f"<ActualReturnRecord id={self.id} company_id={self.company_id} ref='{self.order_reference}' returned={self.was_returned}>"
