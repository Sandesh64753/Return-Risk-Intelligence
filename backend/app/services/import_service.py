import csv
import io
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from app.models.actual_return import ActualReturnRecord
from app.models.product import Product

logger = logging.getLogger("prduct_return_prediction.import_service")

EXPECTED_CSV_HEADERS = [
    "order_reference",
    "product_identifier",
    "product_category",
    "sub_category",
    "brand",
    "product_price",
    "discount_percent",
    "fulfillment_type",
    "payment_method",
    "quantity",
    "defect_rate",
    "order_date",
    "return_date",
    "was_returned",
    "return_reason",
]


class ImportService:
    """Manages secure, company-scoped historical data import with strict validation and idempotency."""

    def get_csv_template_content(self) -> str:
        """Generate a downloadable CSV template with standard header and valid example rows."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(EXPECTED_CSV_HEADERS)
        writer.writerow([
            "ORD-90001",
            "SKU-FASH-01",
            "Fashion",
            "Women",
            "Brand_10",
            "599.0",
            "25.0",
            "Marketplace Fulfilled",
            "Credit Card",
            "1",
            "0.03",
            "2026-09-10",
            "",
            "0",
            "",
        ])
        writer.writerow([
            "ORD-90002",
            "SKU-ELEC-05",
            "Electronics",
            "Laptops",
            "Brand_15",
            "1250.0",
            "15.0",
            "Seller Fulfilled",
            "COD",
            "1",
            "0.08",
            "2026-09-12",
            "2026-09-18",
            "1",
            "Defective trackpad on delivery",
        ])
        return output.getvalue()

    def parse_and_validate_csv(
        self,
        csv_content: str,
        db: Session,
        company_id: int,
        batch_size: int = 500,
    ) -> Dict[str, Any]:
        """Parse, validate, and persist CSV rows scoped strictly to the authenticated company."""
        reader = csv.DictReader(io.StringIO(csv_content))
        if not reader.fieldnames:
            return {
                "success": False,
                "error": "The uploaded CSV file is empty or missing headers.",
                "total_rows": 0,
                "inserted": 0,
                "duplicates": 0,
                "errors": [],
            }

        # Normalize uploaded header names (lowercase, stripped)
        fieldnames = [f.strip().lower() for f in reader.fieldnames if f]
        if "product_category" not in fieldnames or "order_date" not in fieldnames:
            return {
                "success": False,
                "error": "CSV must include at minimum 'product_category' and 'order_date' columns.",
                "total_rows": 0,
                "inserted": 0,
                "duplicates": 0,
                "errors": [],
            }

        # Fetch existing order references for this company to prevent duplicates
        existing_refs = set(
            r[0] for r in (
                db.query(ActualReturnRecord.order_reference)
                .filter(
                    ActualReturnRecord.company_id == company_id,
                    ActualReturnRecord.order_reference.isnot(None),
                )
                .all()
            )
        )

        inserted_count = 0
        duplicate_count = 0
        error_list: List[Dict[str, Any]] = []
        records_to_insert: List[ActualReturnRecord] = []

        row_num = 1  # 1-indexed (header is 1)
        for row in reader:
            row_num += 1
            # Clean keys
            clean_row = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}

            order_ref = clean_row.get("order_reference") or f"IMP-{company_id}-{row_num}"
            if order_ref in existing_refs:
                duplicate_count += 1
                continue

            category = clean_row.get("product_category", "").strip().title()
            if not category:
                error_list.append({"row": row_num, "error": "Missing required product_category."})
                continue

            # Parse order_date
            order_date_str = clean_row.get("order_date", "").strip()
            try:
                parsed_order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
            except ValueError:
                error_list.append({
                    "row": row_num,
                    "error": f"Invalid order_date '{order_date_str}'. Expected YYYY-MM-DD.",
                })
                continue

            # Parse optional return_date
            ret_date_str = clean_row.get("return_date", "").strip()
            parsed_ret_date = None
            if ret_date_str:
                try:
                    parsed_ret_date = datetime.strptime(ret_date_str, "%Y-%m-%d").date()
                except ValueError:
                    error_list.append({
                        "row": row_num,
                        "error": f"Invalid return_date '{ret_date_str}'. Expected YYYY-MM-DD.",
                    })
                    continue

            # Parse was_returned outcome
            was_ret_raw = clean_row.get("was_returned", "").strip()
            was_returned_val = None
            if was_ret_raw in ["1", "true", "True", "yes", "returned"]:
                was_returned_val = 1
            elif was_ret_raw in ["0", "false", "False", "no", "kept"]:
                was_returned_val = 0
            elif was_ret_raw == "":
                was_returned_val = None
            else:
                try:
                    was_returned_val = int(was_ret_raw)
                    if was_returned_val not in (0, 1):
                        was_returned_val = 1 if was_returned_val > 0 else 0
                except ValueError:
                    error_list.append({
                        "row": row_num,
                        "error": f"Invalid was_returned value '{was_ret_raw}'. Expected 0, 1, or blank.",
                    })
                    continue

            # Numerical fields
            price_val = None
            if clean_row.get("product_price"):
                try:
                    price_val = max(0.0, float(clean_row["product_price"]))
                except ValueError:
                    pass

            disc_val = None
            if clean_row.get("discount_percent"):
                try:
                    disc_val = max(0.0, min(100.0, float(clean_row["discount_percent"])))
                except ValueError:
                    pass

            defect_val = None
            if clean_row.get("defect_rate"):
                try:
                    defect_val = max(0.0, min(1.0, float(clean_row["defect_rate"])))
                except ValueError:
                    pass

            qty_val = 1
            if clean_row.get("quantity"):
                try:
                    qty_val = max(1, int(clean_row["quantity"]))
                except ValueError:
                    pass

            sku = clean_row.get("product_identifier") or f"SKU-{category[:4].upper()}"
            sub_cat = clean_row.get("sub_category", "").strip().title() or None
            brand = clean_row.get("brand", "").strip() or None
            fulfillment = clean_row.get("fulfillment_type", "").strip().title() or None
            payment = clean_row.get("payment_method", "").strip() or None
            reason = clean_row.get("return_reason", "").strip() or None

            # Create Record scoped to company
            rec = ActualReturnRecord(
                company_id=company_id,
                order_reference=order_ref,
                product_identifier=sku,
                product_category=category,
                sub_category=sub_cat,
                brand=brand,
                product_price=price_val,
                discount_percent=disc_val,
                fulfillment_type=fulfillment,
                payment_method=payment,
                quantity=qty_val,
                defect_rate=defect_val,
                order_date=parsed_order_date,
                return_date=parsed_ret_date,
                was_returned=was_returned_val,
                return_reason=reason,
                return_status="returned" if was_returned_val == 1 else ("kept" if was_returned_val == 0 else "pending"),
            )
            records_to_insert.append(rec)
            existing_refs.add(order_ref)
            inserted_count += 1

            # Batch write to keep transaction memory bounded
            if len(records_to_insert) >= batch_size:
                db.bulk_save_objects(records_to_insert)
                db.commit()
                records_to_insert = []

        if records_to_insert:
            db.bulk_save_objects(records_to_insert)
            db.commit()

        return {
            "success": True,
            "total_rows": row_num - 1,
            "inserted": inserted_count,
            "duplicates": duplicate_count,
            "errors": error_list[:20],  # Return up to 20 errors for display
            "total_errors": len(error_list),
        }

    def seed_demo_data_for_company(
        self,
        db: Session,
        company_id: int,
        count: int = 150,
    ) -> Dict[str, Any]:
        """Load verified realistic records from repository returns dataset into the company workspace.
        
        This enables immediate realistic exploration of analytics, dashboards, and recommendations.
        """
        import os
        from pathlib import Path

        dataset_path = Path("dataset/cleaned_returns.csv")
        if not dataset_path.exists():
            dataset_path = Path("dataset/returns_dataset.csv")

        if not dataset_path.exists():
            return {"success": False, "error": "Dataset file not found."}

        df = pd.read_csv(dataset_path)
        sample_df = df.sample(min(count, len(df)), random_state=42)

        # Standard return reasons aligned with operational reality
        reasons_pool = [
            "Defective or broken item on delivery",
            "Item did not match website description",
            "Size or fit was smaller than expected",
            "Size or fit was larger than expected",
            "Customer changed mind / no longer needed",
            "Wrong item or color shipped",
            "Packaging crushed and product damaged",
        ]

        today = date.today()
        inserted = 0
        records: List[ActualReturnRecord] = []

        for idx, row in sample_df.iterrows():
            ref = f"ORD-DEMO-{company_id}-{idx}"
            # Spread order dates across the last 90 days
            days_ago = (idx * 7) % 85 + 3
            o_date = today - timedelta(days=days_ago)

            was_ret = int(row.get("returned", 0))
            r_date = None
            reason = None
            if was_ret == 1:
                r_date = o_date + timedelta(days=((idx % 7) + 2))
                reason = reasons_pool[idx % len(reasons_pool)]

            rec = ActualReturnRecord(
                company_id=company_id,
                order_reference=ref,
                product_identifier=f"SKU-{str(row.get('brand', 'BR'))}-{str(row.get('sub_category', 'ITM'))[:3].upper()}",
                product_category=str(row.get("product_category", "Fashion")),
                sub_category=str(row.get("sub_category", "Women")),
                brand=str(row.get("brand", "Brand_10")),
                product_price=float(row.get("product_price", 450.0)),
                discount_percent=float(row.get("discount_percent", 20.0)),
                fulfillment_type=str(row.get("fulfillment_type", "Marketplace Fulfilled")),
                payment_method=str(row.get("payment_method", "Credit Card")),
                quantity=int(row.get("quantity", 1)),
                defect_rate=float(row.get("defect_rate", 0.03)),
                order_date=o_date,
                return_date=r_date,
                was_returned=was_ret,
                return_reason=reason,
                return_status="returned" if was_ret == 1 else "kept",
            )
            records.append(rec)
            inserted += 1

        db.bulk_save_objects(records)
        db.commit()

        return {
            "success": True,
            "inserted": inserted,
        }


import_service = ImportService()
