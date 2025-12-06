import io
from datetime import datetime
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.api.deps import get_db
from app.models.diagnostic import Diagnostic, DiagnosticMethod, MLLabel, QualityGrade
from app.models.object import Object, ObjectType

router = APIRouter()


def _normalize_object_type(raw: str) -> ObjectType:
    """Map raw text to ObjectType, allowing underscores/spaces."""
    value = (raw or "").strip().replace("_", " ").lower()
    for member in ObjectType:
        if member.value.lower() == value:
            return member
    raise ValueError(f"Unknown object_type '{raw}'")


def _normalize_diagnostic_method(raw: str) -> DiagnosticMethod:
    value = (raw or "").strip().upper()
    try:
        return DiagnosticMethod(value)
    except Exception:
        raise ValueError(f"Unknown diagnostic method '{raw}'")


def _normalize_quality_grade(raw: Optional[str]) -> Optional[QualityGrade]:
    if raw is None or str(raw).strip() == "":
        return None
    value = str(raw).strip()
    try:
        return QualityGrade(value)
    except Exception:
        raise ValueError(f"Unknown quality grade '{raw}'")


def _normalize_ml_label(raw: Optional[str]) -> Optional[MLLabel]:
    if raw is None or str(raw).strip() == "":
        return None
    value = str(raw).strip().upper()
    try:
        return MLLabel(value.lower())
    except Exception:
        for member in MLLabel:
            if member.value.upper() == value:
                return member
        raise ValueError(f"Unknown ml_label '{raw}'")


def _to_bool(value: Optional[object]) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"Cannot convert '{value}' to boolean")


def _detect_file_type(columns: List[str]) -> str:
    cols_lower = {c.lower() for c in columns}
    if {"object_id", "lat", "lon"}.issubset(cols_lower):
        return "objects"
    if {"diag_id", "method"}.issubset(cols_lower):
        return "diagnostics"
    raise ValueError("Unknown file format")


def _read_file_to_df(file: UploadFile, content: bytes) -> pd.DataFrame:
    try:
        if file.filename.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(content), engine="openpyxl")
        return pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot parse file: {exc}")


@router.post("/import/")
async def import_objects_csv(file: UploadFile, db: Session = Depends(get_db)):
    """Parse uploaded CSV/XLSX, detect file type, preview, and upsert data."""
    content = await file.read()
    max_size = 5 * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (>5MB)")

    df = _read_file_to_df(file, content)
    columns = list(df.columns)

    try:
        file_type = _detect_file_type(columns)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    created_objects: List[Object] = []
    updated_objects: List[Object] = []
    created_diags: List[Diagnostic] = []
    updated_diags: List[Diagnostic] = []
    errors = []

    if file_type == "objects":
        for idx, row in df.iterrows():
            try:
                obj_type = _normalize_object_type(row.get("object_type", ""))
                data = {
                    "object_name": str(row.get("object_name") or "").strip(),
                    "object_type": obj_type,
                    "pipeline_id": (str(row.get("pipeline_id")) if pd.notna(row.get("pipeline_id")) else "").strip() or None,
                    "lat": float(row.get("lat")),
                    "lon": float(row.get("lon")),
                    "year": int(row.get("year")) if pd.notna(row.get("year")) else None,
                    "material": (str(row.get("material")) if pd.notna(row.get("material")) else "").strip() or None,
                }

                if not data["object_name"]:
                    raise ValueError("object_name is required")

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

    elif file_type == "diagnostics":
        for idx, row in df.iterrows():
            try:
                obj_id = int(row.get("object_id")) if pd.notna(row.get("object_id")) else None
                if obj_id is None:
                    raise ValueError("object_id is required")

                method = _normalize_diagnostic_method(row.get("method"))
                date_val = pd.to_datetime(row.get("date")) if pd.notna(row.get("date")) else None
                if date_val is None:
                    raise ValueError("date is required")

                object_ref = db.get(Object, obj_id)
                if not object_ref:
                    raise ValueError(f"object_id {obj_id} not found")

                data = {
                    "object_id": obj_id,
                    "method": method,
                    "date": date_val.to_pydatetime(),
                    "temperature": float(row.get("temperature")) if pd.notna(row.get("temperature")) else None,
                    "humidity": float(row.get("humidity")) if pd.notna(row.get("humidity")) else None,
                    "illumination": float(row.get("illumination")) if pd.notna(row.get("illumination")) else None,
                    "defect_found": _to_bool(row.get("defect_found")) if pd.notna(row.get("defect_found")) else False,
                    "defect_description": (str(row.get("defect_description")) if pd.notna(row.get("defect_description")) else "").strip() or None,
                    "quality_grade": _normalize_quality_grade(row.get("quality_grade")),
                    "param1": float(row.get("param1")) if pd.notna(row.get("param1")) else None,
                    "param2": float(row.get("param2")) if pd.notna(row.get("param2")) else None,
                    "param3": float(row.get("param3")) if pd.notna(row.get("param3")) else None,
                    "ml_label": _normalize_ml_label(row.get("ml_label")),
                }

                diag_id = int(row.get("diag_id")) if pd.notna(row.get("diag_id")) else None

                if diag_id:
                    existing = db.get(Diagnostic, diag_id)
                    if existing:
                        for k, v in data.items():
                            setattr(existing, k, v)
                        existing.updated_at = datetime.utcnow()
                        updated_diags.append(existing)
                        continue
                    data["diag_id"] = diag_id

                new_diag = Diagnostic(**data)
                created_diags.append(new_diag)
            except Exception as exc:
                errors.append({"row": idx + 2, "error": str(exc)})

        for diag in created_diags:
            db.add(diag)

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to save data: {exc}")

    for obj in created_objects + updated_objects:
        db.refresh(obj)
    for diag in created_diags + updated_diags:
        db.refresh(diag)

    head_df = df.head(5)
    preview_df = head_df.where(pd.notnull(head_df), None)

    return {
        "filename": file.filename,
        "file_type": file_type,
        "columns": columns,
        "preview": preview_df.to_dict(orient="records"),
        "created": len(created_objects) + len(created_diags),
        "updated": len(updated_objects) + len(updated_diags),
        "errors": errors,
    }
