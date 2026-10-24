from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator
import numpy as np

# Validated domain categories from training data
VALID_CATEGORIES = {
    "Beauty": ["Haircare", "Skincare", "Makeup"],
    "Books": ["Fiction", "Non-Fiction", "Academic"],
    "Electronics": ["Laptops", "Mobiles", "Audio"],
    "Fashion": ["Footwear", "Men", "Women", "Kids", "Accessories"],
    "Home": ["Furniture", "Decor", "Kitchen"],
    "Sports": ["Team Sports", "Fitness", "Outdoor"],
    "Toys": ["Educational", "Action Figures", "Outdoor Play"],
}

ALL_PRODUCT_CATEGORIES = sorted(list(VALID_CATEGORIES.keys()))
ALL_SUB_CATEGORIES = sorted(list({sub for subs in VALID_CATEGORIES.values() for sub in subs}))
ALL_BRANDS = [f"Brand_{i}" for i in range(1, 31)]
ALL_FULFILLMENT_TYPES = ["Marketplace Fulfilled", "Seller Fulfilled"]
ALL_PAYMENT_METHODS = ["COD", "Credit Card", "Debit Card", "UPI", "Wallet"]


class PredictionInput(BaseModel):
    product_category: str = Field(
        ...,
        description="Top-level merchandise category (e.g. Fashion, Electronics)",
        examples=["Fashion"]
    )
    sub_category: str = Field(
        ...,
        description="Merchandise sub-category (e.g. Women, Mobiles)",
        examples=["Women"]
    )
    brand: str = Field(
        ...,
        description="Manufacturer or brand identifier (Brand_1 through Brand_30)",
        examples=["Brand_10"]
    )
    product_price: float = Field(
        ...,
        gt=0,
        le=100000.0,
        description="Catalog unit price in currency units",
        examples=[599.0]
    )
    discount_percent: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Promotional discount applied (0.0 to 100.0%)",
        examples=[25.0]
    )
    product_rating: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Average customer product review rating (1.0 to 5.0)",
        examples=[4.2]
    )
    review_count: int = Field(
        ...,
        ge=0,
        le=100000,
        description="Total verified customer reviews",
        examples=[65]
    )
    fragile_item: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 if fragile/breakage-prone merchandise, 0 otherwise",
        examples=[0]
    )
    warranty_available: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 if manufacturer warranty applies, 0 otherwise",
        examples=[1]
    )
    defect_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Historical manufacturer defect rate (0.0 to 1.0)",
        examples=[0.03]
    )
    seller_rating: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="Merchant historical quality rating (1.0 to 5.0)",
        examples=[4.5]
    )
    fulfillment_type: str = Field(
        ...,
        description="Logistics channel ('Marketplace Fulfilled' or 'Seller Fulfilled')",
        examples=["Marketplace Fulfilled"]
    )
    payment_method: str = Field(
        ...,
        description="Order checkout payment method (COD, Credit Card, Debit Card, UPI, Wallet)",
        examples=["Credit Card"]
    )
    quantity: int = Field(
        ...,
        ge=1,
        le=100,
        description="Units purchased in this shipment",
        examples=[1]
    )
    shipping_distance_km: float = Field(
        ...,
        gt=0,
        le=15000.0,
        description="Transit distance between fulfillment hub and destination (km)",
        examples=[350.0]
    )
    wishlist_before_purchase: int = Field(
        ...,
        ge=0,
        le=1,
        description="1 if buyer added product to wishlist prior to ordering, 0 otherwise",
        examples=[1]
    )
    product_page_views: int = Field(
        ...,
        ge=1,
        le=10000,
        description="Product detail page impressions before purchase",
        examples=[15]
    )
    log_price: Optional[float] = Field(
        None,
        description="Optional log1p(product_price). Computed automatically if omitted.",
        examples=[6.3969]
    )
    product_identifier: Optional[str] = Field(
        None,
        description="Optional company SKU or product code for catalog linkage.",
        examples=["SKU-FASH-100"]
    )

    @field_validator("product_category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        cleaned = v.strip().title()
        if cleaned not in ALL_PRODUCT_CATEGORIES:
            pass
        return cleaned

    @field_validator("fulfillment_type")
    @classmethod
    def validate_fulfillment(cls, v: str) -> str:
        cleaned = v.strip().title()
        return cleaned

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, v: str) -> str:
        return v.strip()

    @field_validator("sub_category")
    @classmethod
    def validate_sub_category(cls, v: str) -> str:
        return v.strip().title()

    @field_validator("payment_method")
    @classmethod
    def validate_payment(cls, v: str) -> str:
        cleaned = v.strip()
        for standard in ALL_PAYMENT_METHODS:
            if standard.lower() == cleaned.lower():
                return standard
        return cleaned

    def get_features_dict(self) -> Dict[str, Any]:
        """Convert input data to exact feature dictionary matching model schema."""
        log_p = self.log_price if self.log_price is not None else float(np.log1p(self.product_price))
        return {
            "product_category": self.product_category,
            "sub_category": self.sub_category,
            "brand": self.brand,
            "discount_percent": float(self.discount_percent),
            "product_rating": float(self.product_rating),
            "review_count": int(self.review_count),
            "fragile_item": int(self.fragile_item),
            "warranty_available": int(self.warranty_available),
            "defect_rate": float(self.defect_rate),
            "seller_rating": float(self.seller_rating),
            "fulfillment_type": self.fulfillment_type,
            "payment_method": self.payment_method,
            "quantity": int(self.quantity),
            "shipping_distance_km": float(self.shipping_distance_km),
            "wishlist_before_purchase": int(self.wishlist_before_purchase),
            "product_page_views": int(self.product_page_views),
            "log_price": log_p,
        }


class HistoricalComparison(BaseModel):
    """Contextual historical performance comparison for an evaluated order."""
    category: str
    has_category_history: bool = False
    historical_actual_return_rate: Optional[float] = None
    historical_order_count: int = 0
    historical_return_count: int = 0
    historical_avg_predicted_prob: Optional[float] = None
    has_product_history: bool = False
    product_identifier: Optional[str] = None
    product_actual_return_rate: Optional[float] = None
    product_order_count: int = 0
    active_recommendations_count: int = 0
    comparison_notes: List[str] = Field(default_factory=list)


class PredictionResponse(BaseModel):
    predicted_class: int = Field(..., description="Binary return prediction (0 = Low Risk, 1 = High Risk)")
    risk_label: str = Field(..., description="Human-friendly risk category ('Higher return risk' or 'Lower return risk')")
    return_probability: float = Field(..., description="Estimated probability of return (0.0 to 1.0)")
    probability_percent: float = Field(..., description="Estimated probability formatted as percentage")
    threshold: float = Field(..., description="Operational decision threshold applied for classification")
    risk_level: str = Field(..., description="'Low', 'Moderate', 'High', or 'Critical'")
    interpretation: str = Field(..., description="Neutral explanation distinguishing probability from certainty")
    key_factors: List[str] = Field(default_factory=list, description="Factual highlights of submitted order parameters")
    submitted_inputs: Dict[str, Any] = Field(default_factory=dict, description="Summary of input values used for inference")
    record_id: Optional[int] = Field(None, description="Persisted prediction record ID if saved in database")
    comparison: Optional[HistoricalComparison] = Field(None, description="Contextual historical company comparisons")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Application operational status ('healthy' or 'degraded')")
    model_loaded: bool = Field(..., description="True if inference pipeline is in memory and responsive")
    model_name: Optional[str] = Field(None, description="Name of the loaded estimator")
    threshold: Optional[float] = Field(None, description="Active decision threshold")
    feature_count: Optional[int] = Field(None, description="Number of expected features")
    version: str = Field(..., description="Application semantic version")


# Multi-company authentication and account schemas
class CompanyRegisterInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Official company / workspace name")
    email: str = Field(..., min_length=5, max_length=255, description="Company administrative email")
    password: str = Field(..., min_length=8, max_length=128, description="Secure account password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")
    industry: Optional[str] = Field(None, max_length=100, description="Business vertical / industry")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Please provide a valid company email address.")
        return cleaned


class CompanyLoginInput(BaseModel):
    email: str = Field(..., description="Registered company email")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class CompanyResponse(BaseModel):
    id: int
    name: str
    email: str
    industry: Optional[str] = None
    created_at: Any


# Actual return outcome schema
class ActualReturnCreateInput(BaseModel):
    order_reference: Optional[str] = Field(None, max_length=100)
    product_identifier: Optional[str] = Field(None, max_length=100)
    product_category: str = Field(..., max_length=100)
    sub_category: Optional[str] = Field(None, max_length=100)
    brand: Optional[str] = Field(None, max_length=100)
    product_price: Optional[float] = Field(None, ge=0.0)
    discount_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    fulfillment_type: Optional[str] = Field(None, max_length=100)
    payment_method: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(1, ge=1, le=1000)
    defect_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    order_date: str = Field(..., description="YYYY-MM-DD")
    return_date: Optional[str] = Field(None, description="YYYY-MM-DD if returned")
    was_returned: Optional[int] = Field(None, ge=0, le=1, description="1 if returned, 0 if kept, None if pending")
    return_reason: Optional[str] = Field(None, max_length=255)


class RecommendationUpdateInput(BaseModel):
    status: str = Field(..., pattern="^(open|reviewed|implemented|resolved)$")
    review_notes: Optional[str] = Field(None, max_length=2000)
    implementation_date: Optional[str] = Field(None, description="YYYY-MM-DD")
