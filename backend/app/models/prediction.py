import json
from datetime import datetime
from typing import Any, Dict
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    model_version = Column(String(50), nullable=False)
    predicted_return_class = Column(Integer, nullable=False)  # 0 or 1
    predicted_return_probability = Column(Float, nullable=False)
    decision_threshold = Column(Float, nullable=False)
    risk_label = Column(String(50), nullable=False)  # e.g., "Higher return risk", "Lower return risk"
    risk_level = Column(String(50), nullable=False)  # "Low", "Moderate", "High", "Critical"
    input_features = Column(Text, nullable=False)  # JSON-encoded input payload
    prediction_source = Column(String(50), default="manual_form", nullable=False)

    # Relationships
    company = relationship("Company", back_populates="predictions")
    product = relationship("Product", back_populates="predictions")

    def get_features_dict(self) -> Dict[str, Any]:
        """Safely parse input features from stored JSON text."""
        try:
            return json.loads(self.input_features) if self.input_features else {}
        except Exception:
            return {}

    def __repr__(self):
        return f"<PredictionRecord id={self.id} company_id={self.company_id} prob={self.predicted_return_probability:.3f}>"
