from datetime import datetime

import pandas as pd
from fastapi import HTTPException
from sqlmodel import Session

from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect
from app.services.import_helpers import (
    normalize_diagnostic_method,
    normalize_ml_label,
    normalize_quality_grade,
    to_bool,
)


def import_diagnostics(df: pd.DataFrame, db: Session, errors: list) -> tuple[int, int]:
    created_count = 0
    defects_created = 0

    for idx, row in df.iterrows():
        try:
            obj_id = int(row.get("object_id")) if pd.notna(row.get("object_id")) else None
            if obj_id is None:
                raise ValueError("object_id is required")

            if not db.get(Object, obj_id):
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

            insp = Inspection(
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
            try:
                db.add(insp)
                db.flush()  # populate inspection_id
                if defect_found:
                    defect_type = (
                        (str(row.get("defect_type")) if pd.notna(row.get("defect_type")) else "").strip() or None
                    )
                    depth = float(row.get("depth")) if pd.notna(row.get("depth")) else None
                    length = float(row.get("length")) if pd.notna(row.get("length")) else None
                    width = float(row.get("width")) if pd.notna(row.get("width")) else None

                    db.add(
                        Defect(
                            inspection_id=insp.inspection_id,
                            defect_type=defect_type,
                            depth=depth,
                            length=length,
                            width=width,
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow(),
                        )
                    )
                    defects_created += 1

                db.commit()
                db.refresh(insp)
                created_count += 1
            except Exception as commit_exc:
                db.rollback()
                raise commit_exc
        except Exception as exc:
            errors.append({"row": idx + 2, "error": str(exc)})

    return created_count, defects_created
