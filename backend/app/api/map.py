from typing import List, Optional
from datetime import datetime, date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select, and_, or_
from sqlalchemy import func

from app.api.deps import get_db
from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect
from app.models.diagnostic import DiagnosticMethod, MLLabel, QualityGrade

router = APIRouter()


class MapPopupData(BaseModel):
    object_name: str
    object_type: str
    year: Optional[int]
    material: Optional[str]
    last_check_date: Optional[str]
    method: Optional[str]
    quality_grade: Optional[str]
    ml_label: Optional[str]
    max_depth: Optional[float]
    defect_count: int


class MapObjectResponse(BaseModel):
    id: int
    lat: float
    lon: float
    pipeline_id: Optional[str]
    status: str  # "unknown", "clean", "defect"
    criticality: str  # "normal", "medium", "high" based on ml_label or quality_grade
    popup_data: MapPopupData


def get_criticality_color(ml_label: Optional[MLLabel], quality_grade: Optional[QualityGrade], has_defect: bool) -> str:
    """Определяет цвет критичности на основе ml_label или quality_grade"""
    if ml_label:
        return ml_label.value  # "normal", "medium", "high"
    
    if quality_grade:
        if quality_grade == QualityGrade.UNACCEPTABLE:
            return "high"
        elif quality_grade == QualityGrade.REQUIRES_ACTION:
            return "medium"
        elif quality_grade == QualityGrade.ACCEPTABLE:
            return "normal"
        else:
            return "normal"
    
    if has_defect:
        return "medium"
    
    return "normal"


@router.get("/map-objects", response_model=List[MapObjectResponse])
def get_map_objects(
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID (MT-01, MT-02, MT-03)"),
    method: Optional[str] = Query(None, description="Filter by inspection method"),
    date_from: Optional[str] = Query(None, description="Filter by date from (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter by date to (YYYY-MM-DD)"),
    param_min: Optional[float] = Query(None, description="Minimum parameter value (depth)"),
    param_max: Optional[float] = Query(None, description="Maximum parameter value (depth)"),
    db: Session = Depends(get_db),
):
    """Get map objects with filters for visualization"""
    stmt = select(Object)
    if pipeline_id:
        stmt = stmt.where(Object.pipeline_id == pipeline_id)
    objects = db.exec(stmt).all()

    if not objects:
        return []

    object_ids = [obj.object_id for obj in objects if obj.object_id is not None]

    # Get inspections with filters
    inspection_stmt = select(Inspection).where(Inspection.object_id.in_(object_ids))
    
    if method:
        try:
            method_enum = DiagnosticMethod(method.upper())
            inspection_stmt = inspection_stmt.where(Inspection.method == method_enum)
        except ValueError:
            pass
    
    if date_from:
        try:
            date_from_obj = datetime.fromisoformat(date_from)
            inspection_stmt = inspection_stmt.where(Inspection.date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.fromisoformat(date_to)
            inspection_stmt = inspection_stmt.where(Inspection.date <= date_to_obj)
        except ValueError:
            pass
    
    inspection_stmt = inspection_stmt.order_by(Inspection.object_id, Inspection.date.desc())
    inspections = db.exec(inspection_stmt).all()

    # Get latest inspection per object
    latest_by_object = {}
    for insp in inspections:
        if insp.object_id not in latest_by_object:
            latest_by_object[insp.object_id] = insp

    inspection_ids = [
        insp.inspection_id for insp in latest_by_object.values() if insp.inspection_id is not None
    ]
    
    # Get defects for inspections
    defects_by_inspection = {}
    if inspection_ids:
        defect_stmt = select(Defect).where(Defect.inspection_id.in_(inspection_ids))
        
        # Filter by depth (param1-param3 equivalent)
        if param_min is not None or param_max is not None:
            conditions = []
            if param_min is not None:
                conditions.append(Defect.depth >= param_min)
            if param_max is not None:
                conditions.append(Defect.depth <= param_max)
            if conditions:
                defect_stmt = defect_stmt.where(and_(*conditions))
        
        defects = db.exec(defect_stmt).all()
        for defect in defects:
            if defect.inspection_id not in defects_by_inspection:
                defects_by_inspection[defect.inspection_id] = []
            defects_by_inspection[defect.inspection_id].append(defect)

    results: List[MapObjectResponse] = []
    for obj in objects:
        insp = latest_by_object.get(obj.object_id)
        
        if not insp:
            status = "unknown"
            criticality = "normal"
            last_check_date = None
            method_val = None
            quality_grade_val = None
            ml_label_val = None
            max_depth = None
            defect_count = 0
        else:
            defects = defects_by_inspection.get(insp.inspection_id, [])
            has_defect = len(defects) > 0
            status = "defect" if has_defect else "clean"
            
            criticality = get_criticality_color(insp.ml_label, insp.quality_grade, has_defect)
            last_check_date = insp.date.date().isoformat() if insp.date else None
            method_val = insp.method.value if insp.method else None
            quality_grade_val = insp.quality_grade.value if insp.quality_grade else None
            ml_label_val = insp.ml_label.value if insp.ml_label else None
            max_depth = max((d.depth or 0.0) for d in defects) if defects else None
            defect_count = len(defects)

        results.append(
            MapObjectResponse(
                id=obj.object_id,
                lat=obj.lat,
                lon=obj.lon,
                pipeline_id=obj.pipeline_id,
                status=status,
                criticality=criticality,
                popup_data=MapPopupData(
                    object_name=obj.object_name,
                    object_type=obj.object_type.value,
                    year=obj.year,
                    material=obj.material,
                    last_check_date=last_check_date,
                    method=method_val,
                    quality_grade=quality_grade_val,
                    ml_label=ml_label_val,
                    max_depth=max_depth,
                    defect_count=defect_count,
                ),
            )
        )

    return results
