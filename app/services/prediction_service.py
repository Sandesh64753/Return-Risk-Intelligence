import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd

from app.config import settings
from app.schemas import PredictionInput, PredictionResponse

logger = logging.getLogger("prduct_return_prediction.prediction_service")


class PredictionService:
    """Service encapsulating the trained machine learning pipeline and inference execution."""

    def __init__(self, artifact_path: Optional[Path] = None):
        self.artifact_path = Path(artifact_path) if artifact_path else settings.ARTIFACT_PATH
        self.model_bundle: Optional[Dict[str, Any]] = None
        self.pipeline: Optional[Any] = None
        self.threshold: float = settings.DEFAULT_THRESHOLD
        self.expected_features: List[str] = []
        self.model_name: str = "Unknown"
        self.metrics: Dict[str, Any] = {}
        self.is_loaded: bool = False
        self._load_artifact()

    def _load_artifact(self) -> None:
        """Load and validate the serialized model bundle."""
        if not self.artifact_path.exists():
            logger.error(f"Model artifact not found at {self.artifact_path}")
            self.is_loaded = False
            return

        try:
            bundle = joblib.load(self.artifact_path)
            if not isinstance(bundle, dict):
                raise ValueError(
                    f"Expected artifact to be a dictionary bundle, got {type(bundle)}"
                )

            if "model" not in bundle:
                raise KeyError("Missing 'model' key in serialized bundle.")

            self.model_bundle = bundle
            self.pipeline = bundle["model"]
            self.model_name = bundle.get("model_name", "Logistic Regression")
            self.expected_features = bundle.get("features", [])
            self.metrics = bundle.get("metrics", {})

            # Set threshold from config override if provided, otherwise from artifact
            if settings.OVERRIDE_THRESHOLD is not None:
                self.threshold = float(settings.OVERRIDE_THRESHOLD)
                logger.info(f"Using threshold override from settings: {self.threshold:.4f}")
            else:
                self.threshold = float(bundle.get("threshold", settings.DEFAULT_THRESHOLD))
                logger.info(f"Using threshold from artifact: {self.threshold:.4f}")

            self.is_loaded = True
            logger.info(
                f"Successfully loaded model '{self.model_name}' with {len(self.expected_features)} features."
            )
        except Exception as e:
            logger.exception(f"Failed to load model artifact from {self.artifact_path}: {e}")
            self.is_loaded = False

    def is_ready(self) -> bool:
        """Check if model is loaded and ready for inference."""
        return self.is_loaded and self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Return non-sensitive model metadata for health/info endpoints."""
        return {
            "model_name": self.model_name,
            "threshold": self.threshold,
            "features": self.expected_features,
            "metrics": self.metrics,
            "is_ready": self.is_ready(),
            "target": self.model_bundle.get("target", "returned") if self.model_bundle else "returned",
            "prediction_timing": self.model_bundle.get("prediction_timing", "before shipping") if self.model_bundle else "before shipping",
        }

    def predict(
        self,
        input_data: PredictionInput,
        db: Optional[Any] = None,
        company_id: Optional[int] = None,
        source: str = "manual_form",
    ) -> PredictionResponse:
        """Run ML inference for a single input record and return a structured prediction."""
        if not self.is_ready():
            raise RuntimeError("Prediction service is not initialized: model artifact is not loaded.")

        feature_dict = input_data.get_features_dict()

        # Build DataFrame with exact feature columns in expected order
        df = pd.DataFrame([feature_dict])
        if self.expected_features:
            missing_cols = set(self.expected_features) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required feature columns: {missing_cols}")
            df = df[self.expected_features]

        # Compute prediction probability using fitted pipeline
        try:
            probabilities = self.pipeline.predict_proba(df)
            prob_returned = float(probabilities[0, 1])
        except Exception as e:
            logger.exception(f"Inference execution failed: {e}")
            raise RuntimeError(f"Model inference failed: {str(e)}") from e

        # Apply operational decision threshold
        is_high_risk = prob_returned >= self.threshold
        predicted_class = 1 if is_high_risk else 0
        risk_label = "Higher return risk" if is_high_risk else "Lower return risk"

        # Determine qualitative risk level
        if prob_returned < 0.20:
            risk_level = "Low"
        elif prob_returned < self.threshold:
            risk_level = "Moderate"
        elif prob_returned < 0.70:
            risk_level = "High"
        else:
            risk_level = "Critical"

        # Neutral, grounded interpretation distinguishing probability from certainty
        prob_pct = round(prob_returned * 100, 1)
        thresh_pct = round(self.threshold * 100, 1)

        if is_high_risk:
            interpretation = (
                f"The estimated return probability ({prob_pct}%) meets or exceeds the operational "
                f"decision threshold of {thresh_pct}%. This order has an elevated likelihood of being "
                f"returned based on historical shipping, category, and catalog patterns."
            )
        else:
            interpretation = (
                f"The estimated return probability ({prob_pct}%) is below the operational decision "
                f"threshold of {thresh_pct}%. Historical order and catalog attributes do not indicate "
                f"an elevated risk of return prior to fulfillment."
            )

        # Grounded key operational factors (derived strictly from submitted values)
        factors: List[str] = []
        if input_data.payment_method.upper() == "COD":
            factors.append("Cash on Delivery (COD) payment method historically exhibits higher return rates.")
        if input_data.defect_rate >= 0.08:
            factors.append(f"Elevated manufacturer defect rate ({input_data.defect_rate:.1%}).")
        if input_data.discount_percent >= 40.0:
            factors.append(f"Substantial promotional discount ({input_data.discount_percent:.0f}%) applied.")
        if input_data.fragile_item == 1:
            factors.append("Fragile item designation requires reinforced protective packaging.")
        if input_data.fulfillment_type.lower().startswith("seller"):
            factors.append("Seller-fulfilled logistics routing.")
        if input_data.shipping_distance_km >= 1000.0:
            factors.append(f"Long-haul transit distance ({input_data.shipping_distance_km:.0f} km).")
        if input_data.product_rating < 3.5:
            factors.append(f"Below-average customer product rating ({input_data.product_rating:.1f}/5.0).")
        if input_data.warranty_available == 0:
            factors.append("No manufacturer warranty coverage.")
        if input_data.wishlist_before_purchase == 1:
            factors.append("Item was pre-saved to customer wishlist prior to purchase.")

        # Build clean summary of inputs for display
        submitted_summary = {
            "Product Category": input_data.product_category,
            "Sub-Category": input_data.sub_category,
            "Brand": input_data.brand,
            "Product Price": f"${input_data.product_price:,.2f}",
            "Discount": f"{input_data.discount_percent:.1f}%",
            "Product Rating": f"{input_data.product_rating:.1f} / 5.0",
            "Review Count": f"{input_data.review_count:,}",
            "Fragile Item": "Yes" if input_data.fragile_item else "No",
            "Warranty Available": "Yes" if input_data.warranty_available else "No",
            "Defect Rate": f"{input_data.defect_rate:.1%}",
            "Seller Rating": f"{input_data.seller_rating:.1f} / 5.0",
            "Fulfillment Type": input_data.fulfillment_type,
            "Payment Method": input_data.payment_method,
            "Order Quantity": str(input_data.quantity),
            "Shipping Distance": f"{input_data.shipping_distance_km:,.1f} km",
            "Wishlist Prior to Order": "Yes" if input_data.wishlist_before_purchase else "No",
            "Product Page Views": str(input_data.product_page_views),
        }

        # Optional persistence and historical comparison when db session & company are supplied
        record_id = None
        comparison = None

        if db is not None and company_id is not None:
            import json
            from app.models.prediction import PredictionRecord
            from app.models.product import Product
            from app.services.analytics_service import analytics_service

            product_id = None
            sku = input_data.product_identifier
            if sku:
                # Link or register product in company catalog
                prod = (
                    db.query(Product)
                    .filter(
                        Product.company_id == company_id,
                        Product.product_identifier == sku,
                    )
                    .first()
                )
                if not prod:
                    prod = Product(
                        company_id=company_id,
                        product_identifier=sku,
                        product_name=f"{input_data.brand} {input_data.sub_category}",
                        category=input_data.product_category,
                        sub_category=input_data.sub_category,
                        brand=input_data.brand,
                    )
                    db.add(prod)
                    db.flush()
                product_id = prod.id

            # Save prediction record scoped to company
            pred_record = PredictionRecord(
                company_id=company_id,
                product_id=product_id,
                model_version=self.model_name,
                predicted_return_class=predicted_class,
                predicted_return_probability=round(prob_returned, 4),
                decision_threshold=round(self.threshold, 4),
                risk_label=risk_label,
                risk_level=risk_level,
                input_features=json.dumps(feature_dict),
                prediction_source=source,
            )
            db.add(pred_record)
            db.commit()
            db.refresh(pred_record)
            record_id = pred_record.id

            # Fetch grounded historical company comparison
            comparison = analytics_service.get_historical_context_for_prediction(
                db=db,
                company_id=company_id,
                category=input_data.product_category,
                sku=sku,
            )

        return PredictionResponse(
            predicted_class=predicted_class,
            risk_label=risk_label,
            return_probability=round(prob_returned, 4),
            probability_percent=prob_pct,
            threshold=round(self.threshold, 4),
            risk_level=risk_level,
            interpretation=interpretation,
            key_factors=factors,
            submitted_inputs=submitted_summary,
            record_id=record_id,
            comparison=comparison,
        )


# Global singleton instance loaded once during startup
prediction_service = PredictionService()
