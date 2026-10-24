import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline

from app.config import settings
from app.schemas import PredictionInput, PredictionResponse

logger = logging.getLogger("prduct_return_prediction.prediction_service")

# Exact training-set statistics fitted on non-leakage train split from Capstone Solutions
CAPSTONE_MEDIANS = {
    "product_rating": 3.9,
    "product_return_rate": 0.134,
    "category_return_rate": 0.120,
    "defect_rate": 0.051,
    "seller_rating": 4.1,
    "seller_return_rate": 0.121,
    "shipping_distance_km": 714.1,
    "total_support_contacts": 1.0,
    "fragile_item": 0.0,
    "warranty_available": 0.0,
    "delayed_delivery": 0.0,
}

CAPSTONE_SCALER_MEANS = {
    "product_rating": 3.8819912775236673,
    "product_return_rate": 0.132896875,
    "category_return_rate": 0.1204,
    "defect_rate": 0.06012166666666667,
    "seller_rating": 4.093259259259259,
    "seller_return_rate": 0.1209075,
    "shipping_distance_km": 716.5274447949527,
    "total_support_contacts": 0.8,
}

CAPSTONE_SCALER_SCALES = {
    "product_rating": 0.6364442498692685,
    "product_return_rate": 0.06985929005437316,
    "category_return_rate": 0.04937682908004523,
    "defect_rate": 0.04241432773512062,
    "seller_rating": 0.4669364996328713,
    "seller_return_rate": 0.0583264929263138,
    "shipping_distance_km": 410.7346588066262,
    "total_support_contacts": 0.8968695557326049,
}

CAPSTONE_FEATURE_ORDER = [
    "product_rating",
    "fragile_item",
    "warranty_available",
    "product_return_rate",
    "category_return_rate",
    "defect_rate",
    "seller_rating",
    "seller_return_rate",
    "shipping_distance_km",
    "delayed_delivery",
    "total_support_contacts",
    "brand_Brand_1",
    "brand_Brand_10",
    "brand_Brand_11",
    "brand_Brand_12",
    "brand_Brand_13",
    "brand_Brand_14",
    "brand_Brand_15",
    "brand_Brand_16",
    "brand_Brand_17",
    "brand_Brand_18",
    "brand_Brand_19",
    "brand_Brand_2",
    "brand_Brand_20",
    "brand_Brand_21",
    "brand_Brand_22",
    "brand_Brand_23",
    "brand_Brand_24",
    "brand_Brand_25",
    "brand_Brand_26",
    "brand_Brand_27",
    "brand_Brand_28",
    "brand_Brand_29",
    "brand_Brand_3",
    "brand_Brand_30",
    "brand_Brand_4",
    "brand_Brand_5",
    "brand_Brand_6",
    "brand_Brand_7",
    "brand_Brand_8",
    "brand_Brand_9",
    "fulfillment_type_Marketplace Fulfilled",
    "fulfillment_type_Seller Fulfilled",
    "payment_method_COD",
    "payment_method_Credit Card",
    "payment_method_Debit Card",
    "payment_method_UPI",
    "payment_method_Wallet",
]

DEFAULT_RAW_FEATURES = [
    "product_category",
    "sub_category",
    "brand",
    "product_price",
    "discount_percent",
    "product_rating",
    "review_count",
    "fragile_item",
    "warranty_available",
    "defect_rate",
    "seller_rating",
    "fulfillment_type",
    "payment_method",
    "quantity",
    "shipping_distance_km",
    "wishlist_before_purchase",
    "product_page_views",
]


class CapstoneFeatureTransformer(BaseEstimator, TransformerMixin):
    """Scikit-learn compatible transformer implementing the exact Capstone Model I pipeline:

    - Prunes collinear / zero-signal features identified in Capstone Exercises 1-4 & 6.
    - Merges customer calls + chats into total_support_contacts (Exercise 4).
    - Median imputes missing numeric/binary values.
    - Normalizes numeric columns with fitted StandardScaler statistics.
    - One-hot encodes brand (30 dummies), fulfillment_type (2 dummies), payment_method (5 dummies).
    """

    def __init__(
        self,
        feature_columns: Optional[List[str]] = None,
        train_medians: Optional[Dict[str, float]] = None,
        scaler_means: Optional[Dict[str, float]] = None,
        scaler_scales: Optional[Dict[str, float]] = None,
    ):
        self.feature_columns = feature_columns or CAPSTONE_FEATURE_ORDER
        self.train_medians = train_medians or CAPSTONE_MEDIANS
        self.scaler_means = scaler_means or CAPSTONE_SCALER_MEANS
        self.scaler_scales = scaler_scales or CAPSTONE_SCALER_SCALES

    def fit(self, X: Any, y: Any = None) -> "CapstoneFeatureTransformer":
        return self

    def transform(self, X: Any) -> pd.DataFrame:
        if isinstance(X, dict):
            df_in = pd.DataFrame([X])
        elif isinstance(X, pd.DataFrame):
            df_in = X.copy()
        else:
            df_in = pd.DataFrame(X)

        # If X is already preprocessed into the 48 design columns, return as-is
        if set(self.feature_columns).issubset(set(df_in.columns)):
            return df_in[self.feature_columns]

        out_rows: List[Dict[str, Any]] = []
        for _, row in df_in.iterrows():
            d = row.to_dict()
            res: Dict[str, Any] = {}

            # Support contacts consolidation
            if d.get("total_support_contacts") is not None and not (
                isinstance(d["total_support_contacts"], float) and np.isnan(d["total_support_contacts"])
            ):
                total_sup = float(d["total_support_contacts"])
            else:
                calls = float(d.get("customer_support_calls") or 0.0)
                chats = float(d.get("chat_interactions") or 0.0)
                total_sup = calls + chats if (calls + chats > 0) else self.train_medians.get("total_support_contacts", 1.0)

            # Scaled numeric features
            for col, mean_val in self.scaler_means.items():
                if col == "total_support_contacts":
                    val = total_sup
                else:
                    raw_val = d.get(col)
                    if raw_val is None or (isinstance(raw_val, float) and np.isnan(raw_val)):
                        val = self.train_medians.get(col, 0.0)
                    else:
                        val = float(raw_val)
                scale_val = self.scaler_scales[col]
                res[col] = (val - mean_val) / scale_val

            # Binary indicators
            for col in ["fragile_item", "warranty_available", "delayed_delivery"]:
                val = d.get(col)
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    val = self.train_medians.get(col, 0.0)
                res[col] = int(val)

            # Brand dummies
            brand_val = str(d.get("brand") or "").strip()
            for col in self.feature_columns:
                if col.startswith("brand_"):
                    res[col] = 1 if brand_val == col[6:] else 0

            # Fulfillment type dummies
            ful_val = str(d.get("fulfillment_type") or "").strip().title()
            for col in self.feature_columns:
                if col.startswith("fulfillment_type_"):
                    res[col] = 1 if ful_val == col[17:] else 0

            # Payment method dummies
            pay_val = str(d.get("payment_method") or "").strip().upper()
            for col in self.feature_columns:
                if col.startswith("payment_method_"):
                    res[col] = 1 if pay_val == col[15:].upper() else 0

            out_rows.append(res)

        return pd.DataFrame(out_rows)[self.feature_columns]


class PredictionService:
    """Service encapsulating the trained machine learning pipeline and inference execution."""

    def __init__(self, artifact_path: Optional[Path] = None):
        self.artifact_path = Path(artifact_path) if artifact_path else settings.ARTIFACT_PATH
        self.model_bundle: Optional[Dict[str, Any]] = None
        self.pipeline: Optional[Any] = None
        self.threshold: float = settings.DEFAULT_THRESHOLD
        self.expected_features: List[str] = DEFAULT_RAW_FEATURES
        self.model_name: str = "Logistic Regression"
        self.metrics: Dict[str, Any] = {}
        self.is_loaded: bool = False
        self._load_artifact()

    def _load_artifact(self) -> None:
        """Load and validate the serialized model bundle and build inference pipeline."""
        path_to_try = self.artifact_path
        if not path_to_try.exists():
            candidates = [
                settings.BASE_DIR / "artifacts" / "model.joblib",
                settings.BASE_DIR / "artifacts" / "product_return_prediction.joblib",
                settings.BASE_DIR.parent / "artifacts" / "model.joblib",
                settings.BASE_DIR.parent / "artifacts" / "product_return_prediction.joblib",
            ]
            for cand in candidates:
                if cand.exists():
                    path_to_try = cand
                    break

        if not path_to_try.exists():
            logger.error(f"Model artifact not found at {self.artifact_path} or candidate fallback paths.")
            self.is_loaded = False
            return

        try:
            loaded = joblib.load(path_to_try)

            if isinstance(loaded, dict):
                self.model_bundle = loaded
                raw_model = loaded.get("model")
                self.model_name = loaded.get("model_name", "Logistic Regression")
                self.expected_features = loaded.get("features", DEFAULT_RAW_FEATURES)
                self.metrics = loaded.get("metrics", {"F1": 0.7933, "ROC_AUC": 0.9366})
                design_cols = loaded.get("design_features", CAPSTONE_FEATURE_ORDER)
                medians = loaded.get("train_medians", CAPSTONE_MEDIANS)
                means = loaded.get("scaler_means", CAPSTONE_SCALER_MEANS)
                scales = loaded.get("scaler_scales", CAPSTONE_SCALER_SCALES)

                if settings.OVERRIDE_THRESHOLD is not None:
                    self.threshold = float(settings.OVERRIDE_THRESHOLD)
                else:
                    self.threshold = float(loaded.get("threshold", settings.DEFAULT_THRESHOLD))
            else:
                raw_model = loaded
                self.model_name = "Logistic Regression"
                self.expected_features = DEFAULT_RAW_FEATURES
                self.metrics = {"F1": 0.7933, "ROC_AUC": 0.9366}
                design_cols = getattr(loaded, "feature_names_in_", CAPSTONE_FEATURE_ORDER)
                medians = CAPSTONE_MEDIANS
                means = CAPSTONE_SCALER_MEANS
                scales = CAPSTONE_SCALER_SCALES
                self.threshold = (
                    float(settings.OVERRIDE_THRESHOLD)
                    if settings.OVERRIDE_THRESHOLD is not None
                    else settings.DEFAULT_THRESHOLD
                )

            # Build unified Scikit-Learn Pipeline combining the Capstone feature transformer with the estimator
            transformer = CapstoneFeatureTransformer(
                feature_columns=list(design_cols),
                train_medians=medians,
                scaler_means=means,
                scaler_scales=scales,
            )
            self.pipeline = Pipeline([
                ("preprocessor", transformer),
                ("classifier", raw_model),
            ])

            self.is_loaded = True
            logger.info(
                f"Successfully loaded model '{self.model_name}' from {path_to_try} "
                f"with threshold={self.threshold:.4f} and {len(self.expected_features)} expected features."
            )
        except Exception as e:
            logger.exception(f"Failed to load model artifact from {path_to_try}: {e}")
            self.is_loaded = False

    def is_ready(self) -> bool:
        """Check if model is loaded and ready for inference."""
        return self.is_loaded and self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Return non-sensitive model metadata for health/info endpoints."""
        return {
            "model_name": self.model_name,
            "threshold": self.threshold,
            "features": list(self.expected_features),
            "metrics": self.metrics,
            "is_ready": self.is_ready(),
            "target": "returned",
            "prediction_timing": "before shipping",
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
        df_raw = pd.DataFrame([feature_dict])
        if self.expected_features:
            missing_cols = set(self.expected_features) - set(df_raw.columns)
            if missing_cols:
                raise ValueError(f"Missing required feature columns: {missing_cols}")
            df_raw = df_raw[self.expected_features]

        # Compute prediction probability using fitted pipeline
        try:
            probabilities = self.pipeline.predict_proba(df_raw)
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

        # Grounded key operational factors (derived strictly from submitted values & Capstone insights)
        factors: List[str] = []
        if input_data.payment_method.upper() == "COD":
            factors.append("Cash on Delivery (COD) payment method historically exhibits ~50.5% return rate vs ~15.7% for UPI.")
        if input_data.defect_rate >= 0.08:
            factors.append(f"Elevated manufacturer defect rate ({input_data.defect_rate:.1%}).")
        if input_data.discount_percent >= 40.0:
            factors.append(f"Substantial promotional discount ({input_data.discount_percent:.0f}%) applied.")
        if input_data.fragile_item == 1:
            factors.append("Fragile item designation requires reinforced protective packaging.")
        if input_data.fulfillment_type.lower().startswith("seller"):
            factors.append("Seller-fulfilled logistics routing exhibits higher average dispute rates.")
        if input_data.shipping_distance_km >= 1000.0:
            factors.append(f"Long-haul transit distance ({input_data.shipping_distance_km:.0f} km).")
        if input_data.product_rating < 3.5:
            factors.append(f"Below-average customer product rating ({input_data.product_rating:.1f}/5.0).")
        if input_data.warranty_available == 0:
            factors.append("No manufacturer warranty coverage.")
        if input_data.delayed_delivery == 1:
            factors.append("Order experienced shipping or transit delays (major return trigger).")
        total_sup = (input_data.customer_support_calls or 0) + (input_data.chat_interactions or 0)
        if total_sup >= 2:
            factors.append(f"Multiple pre-dispatch customer support touchpoints recorded ({total_sup} interactions).")

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
            "Delayed Delivery": "Yes" if input_data.delayed_delivery else "No",
            "Support Inquiries": str(total_sup),
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
