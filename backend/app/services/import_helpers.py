import io
from typing import List, Optional

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.models.diagnostic import DiagnosticMethod, QualityGrade, MLLabel
from app.models.object import ObjectType


def normalize_object_type(raw: str) -> ObjectType:
    value = (raw or "").strip().replace("_", " ").lower()
    for member in ObjectType:
        if member.value.lower() == value:
            return member
    raise ValueError(f"Unknown object_type '{raw}'")


def normalize_diagnostic_method(raw: str) -> DiagnosticMethod:
    value = (raw or "").strip().upper()
    aliases = {
        "UT": "UZK",
        "УТ": "UZK",
        "УЗК": "UZK",
    }
    value = aliases.get(value, value)
    try:
        return DiagnosticMethod(value)
    except Exception:
        raise ValueError(f"Unknown diagnostic method '{raw}'")


def normalize_quality_grade(raw: Optional[str]) -> Optional[QualityGrade]:
    if raw is None or str(raw).strip() == "":
        return None
    value = str(raw).strip()
    normalized = value.lower().replace(" ", "_")

    aliases: dict[str, QualityGrade] = {
        "удовлетворительно": QualityGrade.SATISFACTORY,
        "требует_мер": QualityGrade.REQUIRES_ACTION,
        "недопустимо": QualityGrade.UNACCEPTABLE,
        "acceptable": QualityGrade.ACCEPTABLE,
        "requires_action": QualityGrade.REQUIRES_ACTION,
        "unacceptable": QualityGrade.UNACCEPTABLE,
        "satisfactory": QualityGrade.SATISFACTORY,
    }
    if normalized in aliases:
        return aliases[normalized]

    for member in QualityGrade:
        if normalized == member.name.lower() or normalized == member.value.lower():
            return member

    raise ValueError(f"Unknown quality grade '{raw}'")


def normalize_ml_label(raw: Optional[str]) -> Optional[MLLabel]:
    """
    ML label is optional: return None when missing or unrecognized, otherwise mapped enum.
    """
    if raw is None or str(raw).strip() == "":
        return None

    value = str(raw).strip().lower()
    for member in MLLabel:
        if member.value.lower() == value:
            return member

    return None


def to_bool(value: Optional[object]) -> bool:
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


def detect_file_type(columns: List[str]) -> str:
    cols_lower = {c.lower() for c in columns}
    if {"object_id", "lat", "lon"}.issubset(cols_lower):
        return "objects"
    if {"diag_id", "method"}.issubset(cols_lower) or {"object_id", "method", "date"}.issubset(cols_lower):
        return "diagnostics"
    raise ValueError("Unknown file format")


def read_file_to_df(file: UploadFile, content: bytes) -> pd.DataFrame:
    try:
        if file.filename.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(content), engine="openpyxl")
        return pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot parse file: {exc}")
