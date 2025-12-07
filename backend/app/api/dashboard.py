from datetime import datetime
from typing import List, Optional
from sqlalchemy import func
from sqlmodel import Session, select
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_db
from app.models.inspection import Inspection
from app.models.defect import Defect
from app.models.object import Object
from app.models.diagnostic import DiagnosticMethod, MLLabel


router = APIRouter()


class DefectByMethod(BaseModel):
    method: str
    count: int


class DefectByCriticality(BaseModel):
    criticality: str
    count: int


class TopRisk(BaseModel):
    object_id: int
    object_name: str
    pipeline_id: Optional[str]
    criticality: Optional[str]
    defect_count: int
    max_depth: Optional[float]


class InspectionsByYear(BaseModel):
    year: int
    count: int


class DashboardStats(BaseModel):
    defects_by_method: List[DefectByMethod]
    defects_by_criticality: List[DefectByCriticality]
    top_risks: List[TopRisk]
    inspections_by_year: List[InspectionsByYear]


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # 1. Распределение дефектов по методам
    # Получаем все дефекты и их инспекции
    all_defects = db.exec(select(Defect)).all()
    inspection_ids = [d.inspection_id for d in all_defects]
    
    method_counts = {}
    if inspection_ids:
        inspections = db.exec(
            select(Inspection).where(Inspection.inspection_id.in_(inspection_ids))
        ).all()
        
        for insp in inspections:
            method = insp.method.value if insp.method else "unknown"
            # Считаем количество дефектов для каждой инспекции этого метода
            defect_count = sum(1 for d in all_defects if d.inspection_id == insp.inspection_id)
            method_counts[method] = method_counts.get(method, 0) + defect_count
    
    defects_by_method = [
        DefectByMethod(method=method, count=count)
        for method, count in sorted(method_counts.items(), key=lambda x: x[1], reverse=True)
    ]
    
    # 2. Распределение по критичности
    # Используем ml_label из Inspection
    criticality_counts = {}
    inspections = db.exec(select(Inspection)).all()
    
    for insp in inspections:
        criticality = insp.ml_label.value if insp.ml_label else "unknown"
        criticality_counts[criticality] = criticality_counts.get(criticality, 0) + 1
    
    defects_by_criticality = [
        DefectByCriticality(criticality=criticality, count=count)
        for criticality, count in sorted(criticality_counts.items())
    ]

    rows = db.exec(
        select(
            Defect,
            Inspection,
            Object
        )
        .join(Inspection, Inspection.inspection_id == Defect.inspection_id)
        .join(Object, Object.object_id == Inspection.object_id)
    ).all()

    risk_map = {}

    for defect, inspection, obj in rows:
        if obj.object_id not in risk_map:
            risk_map[obj.object_id] = {
                "object_id": obj.object_id,
                "object_name": obj.object_name,
                "pipeline_id": obj.pipeline_id,
                "criticality": inspection.ml_label.value if inspection.ml_label else None,
                "defect_count": 0,
                "max_depth": None,
            }

        entry = risk_map[obj.object_id]
        entry["defect_count"] += 1

        if defect.depth is not None:
            entry["max_depth"] = (
                defect.depth if entry["max_depth"] is None 
                else max(entry["max_depth"], defect.depth)
            )

    objects_with_risks = list(risk_map.values())
    
    # Сортируем по критичности (high > medium > normal) и количеству дефектов
    def risk_score(risk):
        crit_score = {"high": 3, "medium": 2, "normal": 1, None: 0}.get(risk["criticality"], 0)
        return (crit_score, risk["defect_count"], risk["max_depth"] or 0)
    
    sorted_risks = sorted(objects_with_risks, key=risk_score, reverse=True)[:5]
    
    top_risks = [
        TopRisk(
            object_id=r["object_id"],
            object_name=r["object_name"],
            pipeline_id=r["pipeline_id"],
            criticality=r["criticality"],
            defect_count=r["defect_count"],
            max_depth=r["max_depth"],
        )
        for r in sorted_risks
    ]
    
    # 4. Количество обследований по годам
    all_inspections = db.exec(select(Inspection)).all()
    year_counts = {}
    for insp in all_inspections:
        year = insp.date.year
        year_counts[year] = year_counts.get(year, 0) + 1
    
    inspections_by_year = [
        InspectionsByYear(year=year, count=count)
        for year, count in sorted(year_counts.items())
    ]
    
    return DashboardStats(
        defects_by_method=defects_by_method,
        defects_by_criticality=defects_by_criticality,
        top_risks=top_risks,
        inspections_by_year=inspections_by_year,
    )

