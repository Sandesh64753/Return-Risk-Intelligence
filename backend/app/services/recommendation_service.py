import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.actual_return import ActualReturnRecord
from app.models.recommendation import RecommendationRecord


class RecommendationService:
    """Transparent, rule-based recommendation engine connecting observed return patterns to actions."""

    def generate_recommendations(self, db: Session, company_id: int) -> List[RecommendationRecord]:
        """Scan company-scoped actual return outcomes and generate/refresh action items."""
        # 1. Total company baseline
        total_known = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .scalar() or 0
        )
        if total_known < 5:
            return []

        total_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
            )
            .scalar() or 0
        )
        baseline_rate = round((total_rets / total_known * 100.0), 1) if total_known > 0 else 0.0

        generated_items: List[Dict[str, Any]] = []

        # Rule 1: High Category Return Rate (>= 10 orders, rate >= 25% or >= 5 pp above baseline)
        cat_stats = (
            db.query(
                ActualReturnRecord.product_category,
                func.count(ActualReturnRecord.id).label("orders"),
                func.sum(ActualReturnRecord.was_returned).label("returns"),
            )
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned.isnot(None),
            )
            .group_by(ActualReturnRecord.product_category)
            .having(func.count(ActualReturnRecord.id) >= 10)
            .all()
        )
        for cat, orders, rets in cat_stats:
            rets_num = int(rets or 0)
            rate = round(rets_num / orders * 100.0, 1)
            if rate >= 25.0 or (rate - baseline_rate >= 5.0):
                evidence = {
                    "metric": "Observed Return Rate",
                    "sample_size": orders,
                    "returns": rets_num,
                    "observed_rate": f"{rate}%",
                    "baseline_rate": f"{baseline_rate}%",
                    "difference_pp": f"+{round(rate - baseline_rate, 1)} pp",
                }
                generated_items.append({
                    "segment_type": "category",
                    "segment_identifier": cat,
                    "category": cat,
                    "sub_category": None,
                    "title": f"Elevated return rate in category: {cat}",
                    "text": (
                        f"The '{cat}' category has an observed return rate of {rate}% across {orders} "
                        f"completed orders, exceeding the overall catalog baseline of {baseline_rate}%."
                    ),
                    "evidence": json.dumps(evidence),
                    "action": (
                        f"Audit product descriptions, imagery, and sizing specifications for '{cat}' listings. "
                        f"Investigate customer return comments to identify discrepancies between listing expectations and delivered items."
                    ),
                })

        # Rule 2: COD Payment Channel Elevated Risk (>= 10 COD orders, COD rate >= baseline + 8 pp)
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
        if cod_orders and cod_orders[0] >= 10:
            c_count = cod_orders[0]
            c_rets = int(cod_orders[1] or 0)
            cod_rate = round(c_rets / c_count * 100.0, 1)
            if cod_rate - baseline_rate >= 8.0:
                evidence = {
                    "metric": "Payment Method Return Rate",
                    "sample_size": c_count,
                    "returns": c_rets,
                    "observed_rate": f"{cod_rate}%",
                    "baseline_rate": f"{baseline_rate}%",
                    "difference_pp": f"+{round(cod_rate - baseline_rate, 1)} pp",
                }
                generated_items.append({
                    "segment_type": "payment_method",
                    "segment_identifier": "COD",
                    "category": None,
                    "sub_category": None,
                    "title": "Cash on Delivery (COD) Return Disparity",
                    "text": (
                        f"Cash on Delivery orders show a {cod_rate}% return/rejection rate across {c_count} orders, "
                        f"which is {round(cod_rate - baseline_rate, 1)} percentage points higher than the overall baseline."
                    ),
                    "evidence": json.dumps(evidence),
                    "action": (
                        "Implement automated pre-dispatch order confirmation via SMS or WhatsApp for COD purchases, "
                        "or test a modest instant-discount incentive to encourage prepaid checkout."
                    ),
                })

        # Rule 3: Defect & Quality Return Reasons (>= 25% of returns citing defect/damage)
        defect_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
                func.lower(ActualReturnRecord.return_reason).like("%defect%") |
                func.lower(ActualReturnRecord.return_reason).like("%damage%") |
                func.lower(ActualReturnRecord.return_reason).like("%broken%"),
            )
            .scalar() or 0
        )
        if total_rets >= 10 and (defect_rets / total_rets) >= 0.25:
            pct_defect = round(defect_rets / total_rets * 100.0, 1)
            evidence = {
                "metric": "Defect / Damage Return Share",
                "sample_size": total_rets,
                "defect_returns": defect_rets,
                "share_of_returns": f"{pct_defect}%",
            }
            generated_items.append({
                "segment_type": "return_reason",
                "segment_identifier": "Defect/Damage",
                "category": None,
                "sub_category": None,
                "title": "High Proportion of Damage or Defect Returns",
                "text": (
                    f"{pct_defect}% of all recorded returns ({defect_rets} out of {total_rets}) "
                    f"cite item damage, manufacturing defects, or broken components as the primary return reason."
                ),
                "evidence": json.dumps(evidence),
                "action": (
                    "Initiate inbound supplier quality checks and review packaging cushioning standards for fulfillment centers. "
                    "Conduct a supplier defect review for batches manufactured in the past quarter."
                ),
            })

        # Rule 4: Sizing & Fit Discrepancies in Fashion / Apparel
        sizing_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
                func.lower(ActualReturnRecord.return_reason).like("%size%") |
                func.lower(ActualReturnRecord.return_reason).like("%fit%"),
            )
            .scalar() or 0
        )
        if total_rets >= 10 and (sizing_rets / total_rets) >= 0.25:
            pct_sizing = round(sizing_rets / total_rets * 100.0, 1)
            evidence = {
                "metric": "Fit / Sizing Return Share",
                "sample_size": total_rets,
                "sizing_returns": sizing_rets,
                "share_of_returns": f"{pct_sizing}%",
            }
            generated_items.append({
                "segment_type": "return_reason",
                "segment_identifier": "Fit/Size",
                "category": "Fashion",
                "sub_category": None,
                "title": "Substantial Returns Attributed to Sizing and Fit",
                "text": (
                    f"{pct_sizing}% of logged returns cite sizing or fit mismatch as the primary driver."
                ),
                "evidence": json.dumps(evidence),
                "action": (
                    "Introduce detailed body measurement charts, customer fit guidelines, and 'true-to-size' indicators on product pages."
                ),
            })

        # Rule 5: Missing Reason Codes in Elevated Return Categories
        no_reason_rets = (
            db.query(func.count(ActualReturnRecord.id))
            .filter(
                ActualReturnRecord.company_id == company_id,
                ActualReturnRecord.was_returned == 1,
                (ActualReturnRecord.return_reason.is_(None) | (ActualReturnRecord.return_reason == "")),
            )
            .scalar() or 0
        )
        if total_rets >= 10 and (no_reason_rets / total_rets) >= 0.40:
            pct_missing = round(no_reason_rets / total_rets * 100.0, 1)
            evidence = {
                "metric": "Unclassified Return Reasons",
                "sample_size": total_rets,
                "unclassified_returns": no_reason_rets,
                "unclassified_share": f"{pct_missing}%",
            }
            generated_items.append({
                "segment_type": "governance",
                "segment_identifier": "Data Collection",
                "category": None,
                "sub_category": None,
                "title": "Elevated Unclassified Return Reason Volume",
                "text": (
                    f"{pct_missing}% of recorded returns ({no_reason_rets} of {total_rets}) have no return reason code attached."
                ),
                "evidence": json.dumps(evidence),
                "action": (
                    "Require structured return reason codes at the time customer initiates return request in your reverse-logistics portal."
                ),
            })

        # Synchronize items into database idempotently
        persisted = []
        for item in generated_items:
            existing = (
                db.query(RecommendationRecord)
                .filter(
                    RecommendationRecord.company_id == company_id,
                    RecommendationRecord.segment_type == item["segment_type"],
                    RecommendationRecord.segment_identifier == item["segment_identifier"],
                )
                .first()
            )
            if existing:
                # Update evidence and texts while preserving company review status and notes
                existing.recommendation_text = item["text"]
                existing.evidence = item["evidence"]
                existing.suggested_action = item["action"]
                existing.updated_at = datetime.utcnow()
                persisted.append(existing)
            else:
                new_rec = RecommendationRecord(
                    company_id=company_id,
                    segment_type=item["segment_type"],
                    segment_identifier=item["segment_identifier"],
                    category=item.get("category"),
                    sub_category=item.get("sub_category"),
                    recommendation_title=item["title"],
                    recommendation_text=item["text"],
                    evidence=item["evidence"],
                    suggested_action=item["action"],
                    status="open",
                )
                db.add(new_rec)
                persisted.append(new_rec)

        db.commit()
        for p in persisted:
            db.refresh(p)
        return persisted

    def get_recommendations(
        self,
        db: Session,
        company_id: int,
        status_filter: Optional[str] = None,
    ) -> List[RecommendationRecord]:
        """Fetch all recommendations for the company with optional status filter."""
        query = db.query(RecommendationRecord).filter(RecommendationRecord.company_id == company_id)
        if status_filter and status_filter != "all":
            query = query.filter(RecommendationRecord.status == status_filter)
        return query.order_by(RecommendationRecord.created_at.desc()).all()

    def update_status(
        self,
        db: Session,
        company_id: int,
        recommendation_id: int,
        new_status: str,
        review_notes: Optional[str] = None,
        implementation_date: Optional[date] = None,
    ) -> Optional[RecommendationRecord]:
        """Update recommendation review status, implementation date, and notes."""
        rec = (
            db.query(RecommendationRecord)
            .filter(
                RecommendationRecord.id == recommendation_id,
                RecommendationRecord.company_id == company_id,
            )
            .first()
        )
        if not rec:
            return None

        rec.status = new_status
        if review_notes is not None:
            rec.review_notes = review_notes
        if new_status == "implemented":
            rec.implementation_date = implementation_date or date.today()
        elif new_status in ["open", "reviewed"]:
            rec.implementation_date = None

        rec.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rec)
        return rec

    def get_implementation_impact(
        self,
        db: Session,
        company_id: int,
        recommendation_id: int,
    ) -> Optional[Dict[str, Any]]:
        """Measure observed return rates before and after recommendation implementation."""
        rec = (
            db.query(RecommendationRecord)
            .filter(
                RecommendationRecord.id == recommendation_id,
                RecommendationRecord.company_id == company_id,
            )
            .first()
        )
        if not rec or not rec.implementation_date:
            return None

        imp_date = rec.implementation_date

        # Scope queries to the affected category or operational segment
        base_query = db.query(ActualReturnRecord).filter(
            ActualReturnRecord.company_id == company_id,
            ActualReturnRecord.was_returned.isnot(None),
        )
        if rec.category:
            base_query = base_query.filter(ActualReturnRecord.product_category == rec.category)
        elif rec.segment_type == "payment_method":
            base_query = base_query.filter(ActualReturnRecord.payment_method == rec.segment_identifier)

        # Before period
        before_orders = base_query.filter(ActualReturnRecord.order_date < imp_date).count()
        before_rets = (
            base_query.filter(
                ActualReturnRecord.order_date < imp_date,
                ActualReturnRecord.was_returned == 1,
            ).count()
        )
        before_rate = round(before_rets / before_orders * 100.0, 1) if before_orders > 0 else 0.0

        # After period
        after_orders = base_query.filter(ActualReturnRecord.order_date >= imp_date).count()
        after_rets = (
            base_query.filter(
                ActualReturnRecord.order_date >= imp_date,
                ActualReturnRecord.was_returned == 1,
            ).count()
        )
        after_rate = round(after_rets / after_orders * 100.0, 1) if after_orders > 0 else 0.0

        diff_pp = round(after_rate - before_rate, 1) if (before_orders > 0 and after_orders > 0) else None

        return {
            "recommendation_id": rec.id,
            "title": rec.recommendation_title,
            "implementation_date": str(imp_date),
            "before_period": {"orders": before_orders, "returns": before_rets, "rate": before_rate},
            "after_period": {"orders": after_orders, "returns": after_rets, "rate": after_rate},
            "difference_pp": diff_pp,
            "has_sufficient_data": before_orders >= 5 and after_orders >= 5,
            "caveat": (
                "Observed changes represent before-and-after associations. Confounding variables such as "
                "seasonal trends, pricing adjustments, or catalog changes may also influence return rates."
            ),
        }


recommendation_service = RecommendationService()
