from datetime import datetime
import logging

import pandas as pd
from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect
from app.services.import_helpers import (
    normalize_diagnostic_method,
    normalize_ml_label,
    normalize_quality_grade,
    to_bool,
)
from app.services.ml_service import ml_service

logger = logging.getLogger(__name__)


def import_diagnostics(df: pd.DataFrame, db: Session, errors: list) -> tuple[int, int]:
    created_count = 0
    inspections_to_add: list[tuple[Inspection, dict | None]] = []

    object_ids: set[int] = set()
    for val in df.get("object_id", []):
        if not pd.notna(val):
            continue
        try:
            object_ids.add(int(val))
        except Exception:
            continue

    existing_object_ids: set[int] = set()
    if object_ids:
        found = db.exec(select(Object.object_id).where(Object.object_id.in_(object_ids))).all()
        existing_object_ids = {row[0] if isinstance(row, tuple) else row for row in found}

    for idx, row in df.iterrows():
        try:
            obj_id = int(row.get("object_id")) if pd.notna(row.get("object_id")) else None
            if obj_id is None:
                raise ValueError("object_id is required")
            if obj_id not in existing_object_ids:
                raise ValueError(f"object_id {obj_id} not found")

            method = normalize_diagnostic_method(row.get("method"))
            date_val = pd.to_datetime(row.get("date")) if pd.notna(row.get("date")) else None
            if date_val is None:
                raise ValueError("date is required")

            temperature = float(row.get("temperature")) if pd.notna(row.get("temperature")) else None
            humidity = float(row.get("humidity")) if pd.notna(row.get("humidity")) else None
            illumination = float(row.get("illumination")) if pd.notna(row.get("illumination")) else None
            quality_grade = normalize_quality_grade(row.get("quality_grade"))
            ml_label = normalize_ml_label(row.get("ml_label"))
            defect_found = to_bool(row.get("defect_found")) if pd.notna(row.get("defect_found")) else False

            inspection = Inspection(
                object_id=obj_id,
                date=date_val.to_pydatetime(),
                method=method,
                temperature=temperature,
                humidity=humidity,
                illumination=illumination,
                quality_grade=quality_grade,
                ml_label=ml_label,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            defect_data = None
            if defect_found:
                defect_data = {
                    "defect_type": (
                        (str(row.get("defect_type")) if pd.notna(row.get("defect_type")) else "").strip() or None
                    ),
                    "depth": float(row.get("depth")) if pd.notna(row.get("depth")) else None,
                    "length": float(row.get("length")) if pd.notna(row.get("length")) else None,
                    "width": float(row.get("width")) if pd.notna(row.get("width")) else None,
                }

            inspections_to_add.append((inspection, defect_data))
            created_count += 1
        except Exception as exc:
            errors.append({"row": idx + 2, "error": str(exc)})

    if not inspections_to_add:
        return 0, 0

    try:
        db.add_all([pair[0] for pair in inspections_to_add])
        db.flush()

        defects_to_add: list[Defect] = []
        for inspection, defect_data in inspections_to_add:
            if defect_data is None:
                continue
            defects_to_add.append(
                Defect(
                    inspection_id=inspection.inspection_id,
                    defect_type=defect_data["defect_type"],
                    depth=defect_data["depth"],
                    length=defect_data["length"],
                    width=defect_data["width"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
            )

        if defects_to_add:
            db.add_all(defects_to_add)

        db.commit()
        defects_created = len([d for _, d in inspections_to_add if d is not None])
        
        # Prepare data for ML training
        try:
            # Build DataFrame from imported inspections with defect data
            ml_df = df[['method', 'temperature', 'humidity', 'illumination', 'param1', 'param2', 'param3', 'defect_found', 'quality_grade', 'date', 'ml_label']]
            labeled_df = ml_df[ml_df['ml_label'].notna()].copy()
            prediction_results = None
            
            if len(labeled_df) > 0:
                print(f"Training ML model on {len(labeled_df)} labeled samples...")
                train_metrics, test_metrics = ml_service.train(labeled_df, db)
                
                if train_metrics:
                    print(f"Model training completed. Train accuracy: {train_metrics.get('accuracy', 0):.4f}, "
                                f"Test accuracy: {test_metrics.get('accuracy', 0):.4f}")
                    
                    # Predict for unlabeled data
                    unlabeled_df = ml_df[ml_df['ml_label'].isna()].copy()
                    if len(unlabeled_df) > 0:
                        print(f"Predicting labels for {len(unlabeled_df)} unlabeled samples...")
                        prediction_results = ml_service.predict_unlabeled(unlabeled_df, db)
                        
                        if prediction_results.get('predicted', 0) > 0:
                            print(f"Predicted labels for {prediction_results['predicted']} unlabeled diagnostics. "
                                        f"Distribution: {prediction_results.get('label_distribution', {})}")
                    
                    # Save metrics to database
                    ml_service.save_metrics(db, train_metrics, test_metrics, prediction_results)
        except Exception as ml_exc:
            logger.error(f"ML service error: {ml_exc}", exc_info=True)
        
        return created_count, defects_created
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to save diagnostics: {exc}")
