from datetime import datetime
from typing import List

import pandas as pd
from fastapi import HTTPException
from sqlmodel import Session

from app.models.object import Object
from app.models.pipeline import Pipeline
from app.services.import_helpers import normalize_object_type


def import_objects(df: pd.DataFrame, db: Session, errors: list) -> tuple[int, int]:
    created_objects: List[Object] = []
    updated_objects: List[Object] = []

    for idx, row in df.iterrows():
        try:
            obj_type = normalize_object_type(row.get("object_type", ""))
            pipeline_value = (
                (str(row.get("pipeline_id")) if pd.notna(row.get("pipeline_id")) else "").strip() or None
            )
            data = {
                "object_name": str(row.get("object_name") or "").strip(),
                "object_type": obj_type,
                "pipeline_id": pipeline_value,
                "lat": float(row.get("lat")),
                "lon": float(row.get("lon")),
                "year": int(row.get("year")) if pd.notna(row.get("year")) else None,
                "material": (str(row.get("material")) if pd.notna(row.get("material")) else "").strip() or None,
            }

            if not data["object_name"]:
                raise ValueError("object_name is required")

            if pipeline_value:
                existing_pipeline = db.get(Pipeline, pipeline_value)
                if not existing_pipeline:
                    db.add(Pipeline(pipeline_id=pipeline_value, description=None))

            obj_id = int(row.get("object_id")) if pd.notna(row.get("object_id")) else None

            if obj_id:
                existing = db.get(Object, obj_id)
                if existing:
                    for k, v in data.items():
                        setattr(existing, k, v)
                    existing.updated_at = datetime.utcnow()
                    updated_objects.append(existing)
                    continue
                data["object_id"] = obj_id

            new_obj = Object(**data)
            created_objects.append(new_obj)
        except Exception as exc:
            errors.append({"row": idx + 2, "error": str(exc)})

    for obj in created_objects:
        db.add(obj)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to save data: {exc}")

    for obj in created_objects + updated_objects:
        db.refresh(obj)

    return len(created_objects), len(updated_objects)
