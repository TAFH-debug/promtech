from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy import func
from app.api.deps import get_db
from app.models.object import Object, ObjectCreate, ObjectUpdate, ObjectRead, ObjectType
from app.models.inspection import Inspection
from app.models.defect import Defect

router = APIRouter()


class ObjectTableRow(BaseModel):
    id: int
    object_name: str
    pipeline_id: Optional[str]
    object_type: str
    last_check_date: Optional[date]
    method: Optional[str]
    status: str
    defect_type: Optional[str]
    max_depth: float


@router.get("/search", response_model=List[ObjectTableRow])
def search_objects(
    search: Optional[str] = Query(None, description="Partial match on object name"),
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID"),
    method: Optional[str] = Query(None, description="Filter by latest inspection method"),
    defect_type: Optional[str] = Query(None, description="Filter by defect type (latest inspection, ILIKE)"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("date", regex="^(date|depth|name)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    stmt = select(Object)
    if pipeline_id:
        stmt = stmt.where(Object.pipeline_id == pipeline_id)
    if search:
        stmt = stmt.where(func.lower(Object.object_name).ilike(f"%{search.lower()}%"))

    objects = db.exec(stmt).all()
    if not objects:
        return []

    object_ids = [obj.object_id for obj in objects if obj.object_id is not None]

    latest_by_object = {}
    if object_ids:
        inspections = db.exec(
            select(Inspection)
            .where(Inspection.object_id.in_(object_ids))
            .order_by(Inspection.object_id, Inspection.date.desc())
        ).all()
        for insp in inspections:
            if insp.object_id not in latest_by_object:
                latest_by_object[insp.object_id] = insp

    inspection_ids = [insp.inspection_id for insp in latest_by_object.values() if insp.inspection_id]
    defects_by_insp = {insp_id: [] for insp_id in inspection_ids}
    if inspection_ids:
        defect_rows = db.exec(select(Defect).where(Defect.inspection_id.in_(inspection_ids))).all()
        for defect in defect_rows:
            defects_by_insp.setdefault(defect.inspection_id, []).append(defect)

    rows: List[ObjectTableRow] = []
    for obj in objects:
        insp = latest_by_object.get(obj.object_id)
        defects = defects_by_insp.get(insp.inspection_id, []) if insp else []

        if method and insp and insp.method.value != method:
            continue

        matched_defects = defects
        if defect_type:
            needle = defect_type.lower()
            matched_defects = [d for d in defects if d.defect_type and needle in d.defect_type.lower()]
            if not matched_defects:
                continue

        has_inspection = insp is not None
        has_defects = bool(matched_defects)
        status = "unknown"
        if has_inspection:
            status = "defect" if has_defects else "clean"

        if matched_defects:
            defect_for_type = max(matched_defects, key=lambda d: d.depth or 0)
            defect_type_val = defect_for_type.defect_type
            max_depth_val = max((d.depth or 0.0) for d in matched_defects)
        else:
            defect_type_val = None
            max_depth_val = 0.0

        last_check_date = insp.date.date() if insp and insp.date else None
        method_val = insp.method.value if insp else None

        rows.append(
            ObjectTableRow(
                id=obj.object_id,
                object_name=obj.object_name,
                pipeline_id=obj.pipeline_id,
                object_type=obj.object_type.value,
                last_check_date=last_check_date,
                method=method_val,
                status=status,
                defect_type=defect_type_val,
                max_depth=max_depth_val,
            )
        )

    reverse = order == "desc"
    if sort_by == "date":
        rows.sort(key=lambda r: (r.last_check_date or date.min), reverse=reverse)
    elif sort_by == "depth":
        rows.sort(key=lambda r: r.max_depth, reverse=reverse)
    elif sort_by == "name":
        rows.sort(key=lambda r: r.object_name.lower(), reverse=reverse)

    start = (page - 1) * size
    end = start + size
    return rows[start:end]


