from datetime import date, datetime, timedelta
import math
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, and_, desc
from sqlalchemy.orm import Session

from app.config import settings
from app.models.actual_return import ActualReturnRecord
from app.models.prediction import PredictionRecord
from app.models.product import Product
from app.models.recommendation import RecommendationRecord
from app.schemas import HistoricalComparison


def calculate_wilson_ci(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Calculate the Wilson score confidence interval for a binomial proportion.
    
    Provides realistic uncertainty boundaries for small and moderate sample sizes.
    Returns (lower_bound_pct, upper_bound_pct).
    """
    if total <= 0:
        return 0.0, 0.0
    z = 1.96 if confidence == 0.95 else 1.645
    p = successes / total
    denominator = 1 + (z ** 2) / total
    center = (p + (z ** 2) / (2 * total)) / denominator
    margin = (z * math.sqrt((p * (1 - p) / total) + ((z ** 2) / (4 * (total ** 2))))) / denominator
    lower = max(0.0, center - margin) * 100.0
    upper = min(1.0, center + margin) * 100.0
    return round(lower, 1), round(upper, 1)


class AnalyticsService:
    """Provides scoped analytics, return rate metrics, and period comparisons for a specific company."""

    def get_dashboard_summary(self, db: Session, company_id: int) -> Dict[str, Any]:
        """Aggregate high-level operational metrics strictly scoped to the authenticated company."""
        # 1. Prediction counts
        total_predictions = (
            db.query(func.count(PredictionRecord.id))
            .filter(PredictionRecord.company_id == company_id)
            .scalar() or 0
        )
        high_risk_predictions = (
            db.query(func.count(PredictionRecord.id))
            .filter(
                PredictionRecord.company_id == company_id,
                PredictionRecord.predicted_return_class == 1,
            )
            .scalar() or 0
        )
        avg_pred_prob = (
            db.query(func.avg(PredictionRecord.predicted_return_probability))
            .filter(PredictionRecord.company_id == company_id)
            .scalar()
        )

        # 2. Actual outcome counts (strictly known outcomes: was_returned is not None)
        total_known_orders = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .scalar() or 0
        )
        actual_returns = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
            )
            .scalar() or 0
        )
        actual_return_rate = (
            round((actual_returns / total_known_orders) * 100.0, 1) if total_known_orders > 0 else 0.0
        )

        # 3. Active recommendations requiring review or action
        active_recs_count = (
            db.query(func.count(RecommendationRecord.id))
            .filter(
                RecommendationRecord.company_id == company_id,
                RecommendationRecord.status.in_(["open", "reviewed"]),
            )
            .scalar() or 0
        )

        # 4. Recent predictions (last 5)
        recent_predictions = (
            db.query(PredictionRecord)
            .filter(PredictionRecord.company_id == company_id)
            .order_by(desc(PredictionRecord.created_at))
            .limit(5)
            .all()
        )

        # 5. Top categories with highest observed return rates (min sample size applied)
        min_samples = settings.DEFAULT_MIN_SAMPLE_SIZE
        category_rows = (
            db.query(
                ActualReturnRecord.product_category,
                func.count(ActualReturnRecord.id).label("total_orders"),
                func.sum(ActualReturnRecord.was_returned).label("returns_count"),
            )
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .group_by(ActualReturnRecord.product_category)
            .having(func.count(ActualReturnRecord.id) >= min_samples)
            .all()
        )

        top_categories = []
        for cat, orders, rets in category_rows:
            rets_num = int(rets or 0)
            rate = round((rets_num / orders) * 100.0, 1)
            ci_low, ci_high = calculate_wilson_ci(rets_num, orders)
            top_categories.append({
                "category": cat,
                "orders": orders,
                "returns": rets_num,
                "return_rate": rate,
                "ci_low": ci_low,
                "ci_high": ci_high,
            })
        top_categories.sort(key=lambda x: x["return_rate"], reverse=True)

        return {
            "total_predictions": total_predictions,
            "high_risk_predictions": high_risk_predictions,
            "high_risk_pct": round((high_risk_predictions / total_predictions * 100.0), 1) if total_predictions > 0 else 0.0,
            "avg_predicted_prob": round(float(avg_pred_prob) * 100.0, 1) if avg_pred_prob is not None else None,
            "total_known_orders": total_known_orders,
            "actual_returns": actual_returns,
            "actual_return_rate": actual_return_rate,
            "active_recs_count": active_recs_count,
            "recent_predictions": recent_predictions,
            "top_categories": top_categories[:5],
            "min_sample_size": min_samples,
            "has_data": total_known_orders > 0 or total_predictions > 0,
        }

    def get_segment_breakdown(
        self,
        db: Session,
        company_id: int,
        segment_field: str = "product_category",
        min_sample_size: int = 5,
    ) -> List[Dict[str, Any]]:
        """Calculate return rate statistics across a specified catalog or operational dimension."""
        # Baseline overall rate for relative comparison
        total_known = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .scalar() or 0
        )
        total_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
            )
            .scalar() or 0
        )
        baseline_rate = (total_rets / total_known * 100.0) if total_known > 0 else 0.0

        # Map allowed grouping columns to prevent injection
        column_map = {
            "product_category": ActualReturnRecord.product_category,
            "sub_category": ActualReturnRecord.sub_category,
            "brand": ActualReturnRecord.brand,
            "product_identifier": ActualReturnRecord.product_identifier,
            "fulfillment_type": ActualReturnRecord.fulfillment_type,
            "payment_method": ActualReturnRecord.payment_method,
            "return_reason": ActualReturnRecord.return_reason,
        }
        col = column_map.get(segment_field, ActualReturnRecord.product_category)

        # For return_reason, we only analyze orders where return_reason is recorded
        query = db.query(
            col.label("segment_value"),
            func.count(ActualReturnRecord.id).label("total_orders"),
            func.sum(ActualReturnRecord.was_returned).label("returns_count"),
        ).filter(
            ActualReturnRecord.company_id == company_id,
            col.isnot(None),
        )

        if segment_field != "return_reason":
            query = query.filter(ActualReturnRecord.was_returned.isnot(None))
        else:
            query = query.filter(ActualReturnRecord.was_returned == 1)

        rows = (
            query.group_by(col)
            .all()
        )

        results = []
        for val, orders, rets in rows:
            if not val:
                continue
            rets_num = int(rets or 0)
            if segment_field == "return_reason":
                # For reasons, denominator is total returns to show reason distribution
                pct = round((orders / total_rets * 100.0), 1) if total_rets > 0 else 0.0
                results.append({
                    "segment": str(val),
                    "orders": orders,
                    "returns": orders,
                    "return_rate": pct,
                    "diff_pp": None,
                    "ci_low": None,
                    "ci_high": None,
                    "is_sparse": orders < min_sample_size,
                    "sample_label": "Reason Share",
                })
            else:
                rate = round((rets_num / orders) * 100.0, 1) if orders > 0 else 0.0
                diff = round(rate - baseline_rate, 1)
                ci_low, ci_high = calculate_wilson_ci(rets_num, orders)
                is_sparse = orders < min_sample_size
                sample_label = "Sparse (< min threshold)" if is_sparse else ("Low volume" if orders < 20 else "Adequate volume")
                results.append({
                    "segment": str(val),
                    "orders": orders,
                    "returns": rets_num,
                    "return_rate": rate,
                    "diff_pp": diff,
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "is_sparse": is_sparse,
                    "sample_label": sample_label,
                })

        # Sort: adequate samples first, then by return rate descending
        results.sort(key=lambda x: (not x["is_sparse"], x["return_rate"]), reverse=True)
        return results

    def get_feature_correlations(self, db: Session, company_id: int) -> List[Dict[str, Any]]:
        """Identify empirical associations between operational factors and return rates."""
        findings = []
        total_known = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .scalar() or 0
        )
        if total_known < 10:
            return findings

        baseline_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
            )
            .scalar() or 0
        )
        baseline_rate = round(baseline_rets / total_known * 100.0, 1)

        # 1. Payment method: COD vs Prepaid
        cod_orders = (
            db.query(
                func.count(ActualReturnRecord.id),
                func.sum(ActualReturnRecord.was_returned),
            )
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.payment_method == "COD",
                ActualReturnRecord.was_returned.isnot(None),
            )
            .first()
        )
        if cod_orders and cod_orders[0] >= 5:
            cod_count = cod_orders[0]
            cod_rets = int(cod_orders[1] or 0)
            cod_rate = round(cod_rets / cod_count * 100.0, 1)
            findings.append({
                "factor": "Payment Method: Cash on Delivery (COD)",
                "sample_size": cod_count,
                "observed_rate": cod_rate,
                "baseline_rate": baseline_rate,
                "difference_pp": round(cod_rate - baseline_rate, 1),
                "interpretation": (
                    f"COD orders exhibit a {cod_rate}% return rate compared to {baseline_rate}% "
                    f"across all payment methods ({'+' if cod_rate >= baseline_rate else ''}{round(cod_rate - baseline_rate, 1)} pp)."
                ),
                "caveat": "Buyer intent and absence of pre-commitment may correlate with higher cancellation or rejection at delivery.",
            })

        # 2. Fulfillment type: Seller Fulfilled vs Marketplace
        seller_orders = (
            db.query(
                func.count(ActualReturnRecord.id),
                func.sum(ActualReturnRecord.was_returned),
            )
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.fulfillment_type == "Seller Fulfilled",
                ActualReturnRecord.was_returned.isnot(None),
            )
            .first()
        )
        if seller_orders and seller_orders[0] >= 5:
            s_count = seller_orders[0]
            s_rets = int(seller_orders[1] or 0)
            s_rate = round(s_rets / s_count * 100.0, 1)
            findings.append({
                "factor": "Fulfillment Channel: Seller Fulfilled",
                "sample_size": s_count,
                "observed_rate": s_rate,
                "baseline_rate": baseline_rate,
                "difference_pp": round(s_rate - baseline_rate, 1),
                "interpretation": (
                    f"Merchant-fulfilled shipments show an observed return rate of {s_rate}%, "
                    f"differing by {'+' if s_rate >= baseline_rate else ''}{round(s_rate - baseline_rate, 1)} pp from overall baseline."
                ),
                "caveat": "Variations in handling times, packaging standards, and transit damage can influence this association.",
            })

        # 3. Discount depth: Deep Discount (>= 40%)
        deep_disc = (
            db.query(
                func.count(ActualReturnRecord.id),
                func.sum(ActualReturnRecord.was_returned),
            )
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.discount_percent >= 40.0,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .first()
        )
        if deep_disc and deep_disc[0] >= 5:
            d_count = deep_disc[0]
            d_rets = int(deep_disc[1] or 0)
            d_rate = round(d_rets / d_count * 100.0, 1)
            findings.append({
                "factor": "Promotional Discount: High Discount (>= 40%)",
                "sample_size": d_count,
                "observed_rate": d_rate,
                "baseline_rate": baseline_rate,
                "difference_pp": round(d_rate - baseline_rate, 1),
                "interpretation": (
                    f"Heavily discounted orders exhibit an observed return rate of {d_rate}% "
                    f"vs {baseline_rate}% baseline."
                ),
                "caveat": "Impulse purchasing during promotional events often correlates with buyer second-guessing after delivery.",
            })

        return findings

    def get_period_comparison(
        self,
        db: Session,
        company_id: int,
        window_days: int = 30,
    ) -> Dict[str, Any]:
        """Compare actual return rates between two equivalent, consecutive observation periods.
        
        Strict definition:
        - Current period: [today - window_days, today]
        - Previous period: [today - 2 * window_days, today - window_days - 1]
        - Numerator: orders actually returned (was_returned == 1)
        - Denominator: orders with known outcomes (was_returned is not None)
        """
        today = date.today()
        current_start = today - timedelta(days=window_days)
        previous_start = current_start - timedelta(days=window_days)
        previous_end = current_start - timedelta(days=1)

        # 1. Current Period Outcomes
        curr_orders = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
                ActualReturnRecord.order_date >= current_start,
                ActualReturnRecord.order_date <= today,
            )
            .scalar() or 0
        )
        curr_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
                ActualReturnRecord.order_date >= current_start,
                ActualReturnRecord.order_date <= today,
            )
            .scalar() or 0
        )
        curr_rate = round(curr_rets / curr_orders * 100.0, 1) if curr_orders > 0 else 0.0

        # 2. Previous Period Outcomes
        prev_orders = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
                ActualReturnRecord.order_date >= previous_start,
                ActualReturnRecord.order_date <= previous_end,
            )
            .scalar() or 0
        )
        prev_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
                ActualReturnRecord.order_date >= previous_start,
                ActualReturnRecord.order_date <= previous_end,
            )
            .scalar() or 0
        )
        prev_rate = round(prev_rets / prev_orders * 100.0, 1) if prev_orders > 0 else 0.0

        # 3. Calculate differences
        has_sufficient_history = curr_orders >= settings.DEFAULT_MIN_SAMPLE_SIZE and prev_orders >= settings.DEFAULT_MIN_SAMPLE_SIZE
        diff_pp = round(curr_rate - prev_rate, 1)
        rel_change_pct = round(((curr_rate - prev_rate) / prev_rate) * 100.0, 1) if prev_rate > 0 else None

        # Determine verdict
        if not has_sufficient_history:
            verdict = "insufficient_data"
            summary_message = "Not enough historical outcome records across both observation windows to evaluate trend."
        elif diff_pp <= -1.0:
            verdict = "improving"
            rel_str = f" (~{abs(rel_change_pct)}% relative reduction)" if rel_change_pct else ""
            summary_message = (
                f"Actual return rate decreased by {abs(diff_pp)} percentage points from {prev_rate}% to {curr_rate}%{rel_str}."
            )
        elif diff_pp >= 1.0:
            verdict = "deteriorating"
            rel_str = f" (~{rel_change_pct}% relative increase)" if rel_change_pct else ""
            summary_message = (
                f"Actual return rate increased by {diff_pp} percentage points from {prev_rate}% to {curr_rate}%{rel_str}."
            )
        else:
            verdict = "stable"
            summary_message = f"Return rate remained stable ({prev_rate}% vs {curr_rate}%, change: {diff_pp} pp)."

        # 4. Multi-month monthly cohort series for trend chart
        monthly_series = self.get_monthly_trend(db, company_id)

        return {
            "window_days": window_days,
            "current_period": {"start": str(current_start), "end": str(today), "orders": curr_orders, "returns": curr_rets, "rate": curr_rate},
            "previous_period": {"start": str(previous_start), "end": str(previous_end), "orders": prev_orders, "returns": prev_rets, "rate": prev_rate},
            "diff_pp": diff_pp,
            "relative_change_pct": rel_change_pct,
            "has_sufficient_history": has_sufficient_history,
            "verdict": verdict,
            "summary_message": summary_message,
            "monthly_series": monthly_series,
        }

    def get_monthly_trend(self, db: Session, company_id: int) -> List[Dict[str, Any]]:
        """Compute monthly return rate cohorts for the authenticated company."""
        # Query distinct year-month groupings
        records = (
            db.query(
                ActualReturnRecord.order_date,
                ActualReturnRecord.was_returned,
            )
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .order_by(ActualReturnRecord.order_date.asc())
            .all()
        )

        month_map: Dict[str, Dict[str, int]] = {}
        for r_date, was_ret in records:
            ym = r_date.strftime("%Y-%m")
            if ym not in month_map:
                month_map[ym] = {"orders": 0, "returns": 0}
            month_map[ym]["orders"] += 1
            if was_ret == 1:
                month_map[ym]["returns"] += 1

        series = []
        for ym in sorted(month_map.keys()):
            o = month_map[ym]["orders"]
            r = month_map[ym]["returns"]
            rate = round(r / o * 100.0, 1) if o > 0 else 0.0
            series.append({
                "period": ym,
                "orders": o,
                "returns": r,
                "return_rate": rate,
            })
        return series

    def get_historical_context_for_prediction(
        self,
        db: Session,
        company_id: int,
        category: str,
        sku: Optional[str] = None,
    ) -> HistoricalComparison:
        """Provide grounded historical context comparing a new prediction with observed records."""
        comparison = HistoricalComparison(category=category)
        notes = []

        # 1. Category historical actual returns
        cat_known = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.product_category == category,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .scalar() or 0
        )
        if cat_known >= settings.DEFAULT_MIN_SAMPLE_SIZE:
            cat_rets = (
                db.query(func.count(ActualReturnRecord.id))
                .filter(
                    ActualReturnRecord.company_id == company_id,
                    ActualReturnRecord.product_category == category,
                    ActualReturnRecord.was_returned == 1,
                )
                .scalar() or 0
            )
            rate = round(cat_rets / cat_known * 100.0, 1)
            comparison.has_category_history = True
            comparison.historical_order_count = cat_known
            comparison.historical_return_count = cat_rets
            comparison.historical_actual_return_rate = rate
            notes.append(
                f"Historical actual return rate for '{category}' is {rate}% across {cat_known} completed orders."
            )

        # 2. Average predicted probability for same category
        avg_cat_pred = (
            db.query(func.avg(PredictionRecord.predicted_return_probability))
            .filter(
                PredictionRecord.company_id == company_id,
                PredictionRecord.input_features.like(f'%"product_category": "{category}"%'),
            )
            .scalar()
        )
        if avg_cat_pred is not None:
            comparison.historical_avg_predicted_prob = round(float(avg_cat_pred) * 100.0, 1)
            notes.append(
                f"Historical model predictions for this category have averaged {comparison.historical_avg_predicted_prob}% return probability."
            )

        # 3. Product-specific history if SKU provided
        if sku:
            comparison.product_identifier = sku
            prod_known = (
                db.query(func.count(ActualReturnRecord.id))
                .filter(
                    ActualReturnRecord.company_id == company_id,
                    ActualReturnRecord.product_identifier == sku,
                    ActualReturnRecord.was_returned.isnot(None),
                )
                .scalar() or 0
            )
            if prod_known >= 3:
                prod_rets = (
                    db.query(func.count(ActualReturnRecord.id))
                    .filter(
                        ActualReturnRecord.company_id == company_id,
                        ActualReturnRecord.product_identifier == sku,
                        ActualReturnRecord.was_returned == 1,
                    )
                    .scalar() or 0
                )
                p_rate = round(prod_rets / prod_known * 100.0, 1)
                comparison.has_product_history = True
                comparison.product_order_count = prod_known
                comparison.product_actual_return_rate = p_rate
                notes.append(
                    f"Product SKU '{sku}' has an observed actual return rate of {p_rate}% ({prod_rets} returns / {prod_known} orders)."
                )

        # 4. Active recommendations in this category
        active_recs = (
            db.query(RecommendationRecord)
            .filter(
                RecommendationRecord.company_id == company_id,
                RecommendationRecord.category == category,
                RecommendationRecord.status.in_(["open", "reviewed"]),
            )
            .all()
        )
        comparison.active_recommendations_count = len(active_recs)
        if active_recs:
            notes.append(
                f"{len(active_recs)} active return reduction recommendation(s) currently open for '{category}'."
            )

        comparison.comparison_notes = notes
        return comparison


analytics_service = AnalyticsService()
