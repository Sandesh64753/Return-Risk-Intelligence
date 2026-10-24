import json
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class RecommendationRecord(Base):
    __tablename__ = "recommendation_records"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)

    category = Column(String(100), nullable=True, index=True)
    sub_category = Column(String(100), nullable=True)
    segment_type = Column(String(50), nullable=False)  # 'category', 'product', 'payment_method', 'fulfillment', 'defect'
    segment_identifier = Column(String(100), nullable=False)  # e.g., 'Fashion', 'Brand_5', 'COD'

    recommendation_title = Column(String(255), nullable=False)
    recommendation_text = Column(Text, nullable=False)
    evidence = Column(Text, nullable=False)  # JSON-encoded metric, sample size, return rate, comparison baseline
    suggested_action = Column(Text, nullable=False)

    status = Column(String(50), default="open", nullable=False)  # 'open', 'reviewed', 'implemented', 'resolved'
    implementation_date = Column(Date, nullable=True)
    review_notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="recommendations")
    product = relationship("Product", back_populates="recommendations")

    def get_evidence_dict(self) -> Dict[str, Any]:
        """Safely parse evidence JSON string."""
        try:
            return json.loads(self.evidence) if self.evidence else {}
        except Exception:
            return {}

    def __repr__(self):
        return f"<RecommendationRecord id={self.id} company_id={self.company_id} title='{self.recommendation_title}' status='{self.status}'>"
