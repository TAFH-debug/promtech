import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlmodel import Session

from app.api.deps import get_db
from app.services.import_helpers import detect_file_type, read_file_to_df
from app.services.objects_importer import import_objects
from app.services.diagnostics_importer import import_diagnostics

router = APIRouter()


@router.post("/import/")
async def import_file(file: UploadFile, db: Session = Depends(get_db)):
    """Parse uploaded CSV/XLSX, detect file type, preview, and ingest data."""
    content = await file.read()
    max_size = 5 * 1024 * 1024  # 5MB
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (>5MB)")

    df = read_file_to_df(file, content)
    columns = list(df.columns)

    try:
        file_type = detect_file_type(columns)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    errors = []
    created = 0
    updated = 0
    defects_created = 0

    if file_type == "objects":
        created, updated = import_objects(df, db, errors)
    elif file_type == "diagnostics":
        required_diag = {"object_id", "method", "date", "defect_found"}
        cols_lower = {c.lower() for c in columns}
        missing = [col for col in required_diag if col not in cols_lower]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required diagnostic columns: {', '.join(missing)}")
        created, defects_created = import_diagnostics(df, db, errors)

    head_df = df.head(5)
    preview_df = head_df.where(pd.notnull(head_df), None)
    # Ensure preview payload is JSON-safe (no NaN/NaT values)
    preview_records = []
    for record in preview_df.to_dict(orient="records"):
        cleaned = {k: (None if pd.isna(v) else v) for k, v in record.items()}
        preview_records.append(cleaned)

    return {
        "filename": file.filename,
        "file_type": file_type,
        "columns": columns,
        "preview": preview_records,
        "created": created,
        "updated": updated,
        "defects_created": defects_created,
        "errors": errors,
    }
