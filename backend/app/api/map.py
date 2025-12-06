from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect

router = APIRouter()


class MapPopupData(BaseModel):
    object_name: str
    object_type: str
    year: Optional[int]
    material: Optional[str]
    last_check_date: Optional[str]


class MapObjectResponse(BaseModel):
    id: int
    lat: float
    lon: float
    pipeline_id: Optional[str]
    status: str
    popup_data: MapPopupData


@router.get("/map-objects", response_model=List[MapObjectResponse])
def get_map_objects(
    pipeline_id: Optional[str] = Query(None, description="Filter by pipeline ID"),
    db: Session = Depends(get_db),
):
    stmt = select(Object)
    if pipeline_id:
        stmt = stmt.where(Object.pipeline_id == pipeline_id)
    objects = db.exec(stmt).all()

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

    inspection_ids = [
        insp.inspection_id for insp in latest_by_object.values() if insp.inspection_id is not None
    ]
    inspections_with_defects = set()
    if inspection_ids:
        defect_rows = db.exec(
            select(Defect.inspection_id).where(Defect.inspection_id.in_(inspection_ids))
        ).all()
        inspections_with_defects = {
            row[0] if isinstance(row, tuple) else row for row in defect_rows
        }

    results: List[MapObjectResponse] = []
    for obj in objects:
        insp = latest_by_object.get(obj.object_id)
        if not insp:
            status = "unknown"
            last_check_date = None
        else:
            has_defect = insp.inspection_id in inspections_with_defects
            status = "defect" if has_defect else "clean"
            last_check_date = insp.date.date().isoformat() if insp.date else None

        results.append(
            MapObjectResponse(
                id=obj.object_id,
                lat=obj.lat,
                lon=obj.lon,
                pipeline_id=obj.pipeline_id,
                status=status,
                popup_data=MapPopupData(
                    object_name=obj.object_name,
                    object_type=obj.object_type.value,
                    year=obj.year,
                    material=obj.material,
                    last_check_date=last_check_date,
                ),
            )
        )

    return results
