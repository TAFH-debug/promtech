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

    try:
        df['object_type'] = df['object_type'].apply(normalize_object_type)
        df['object_type'] = df['object_type'].fillna('pipeline section')
        df['material'] = df['material'].fillna('Unknown')

        pipelines = df['pipeline_id'].dropna().unique().tolist()
        for pipeline_id in pipelines:
            existing_pipeline = db.get(Pipeline, pipeline_id)
            if not existing_pipeline:
                db.add(Pipeline(pipeline_id=pipeline_id, description=None))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error processing pipelines: {exc}")
    
    for i in df[["object_name", "object_type", "pipeline_id", "lat", "lon", "year", "material", "object_id"]].to_dict(orient="records"):
        created_objects.append(Object(**i))

    db.add_all(created_objects)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to save data: {exc}")

    return len(created_objects)
