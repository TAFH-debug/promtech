from datetime import date
from typing import List, Optional, Literal, Tuple

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.pipeline import Pipeline
from app.models.object import Object
from app.models.inspection import Inspection
from app.models.defect import Defect

router = APIRouter()


class ReportHeader(BaseModel):
    pipeline_id: str
    pipeline_name: Optional[str] = None
    inspection_date: Optional[date] = None
    operator: Optional[str] = None
    diameter_mm: Optional[float] = None
    wall_thickness_mm: Optional[float] = None
    steel_grade: Optional[str] = None
    launcher_trap_length_mm: Optional[float] = None
    receiver_trap_length_mm: Optional[float] = None
    required_methods: List[str] = Field(default_factory=list)


class TopDefectSummary(BaseModel):
    anomaly_id: str
    type: Literal["metal_loss", "geometry"]
    depth_mm: Optional[float] = None
    depth_percent: Optional[float] = None
    length_mm: Optional[float] = None
    clock_position: Optional[str] = None
    distance_m: Optional[float] = None
    erf: Optional[float] = None
    immediate_action_required: bool


class ExpressReport(BaseModel):
    header: ReportHeader
    total_anomalies: int
    top_10_critical_defects: List[TopDefectSummary]
    immediate_action_required: bool


class DefectItem(BaseModel):
    anomaly_id: str
    type: Literal["metal_loss", "geometry"]
    distance_m: Optional[float] = None
    clock_position: Optional[str] = None
    depth_mm: Optional[float] = None
    depth_percent: Optional[float] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    erf: Optional[float] = None


class HistogramBin(BaseModel):
    bin_start_mm: float
    bin_end_mm: float
    count: int


class VisualsData(BaseModel):
    map_image_url: Optional[HttpUrl] = None
    xyz_profile: List[Tuple[float, float, float]] = Field(default_factory=list)
    depth_histogram: List[HistogramBin] = Field(default_factory=list)


class FinalReport(BaseModel):
    header: ReportHeader
    total_length_inspected_km: Optional[float] = None
    total_weld_joints: Optional[int] = None
    anomaly_count_metal_loss: int
    anomaly_count_geometry: int
    defects: List[DefectItem]
    visuals: VisualsData


class ERFInputs(BaseModel):
    pressure_operating_mpa: Optional[float] = None
    pressure_max_allowable_mpa: Optional[float] = None
    diameter_mm: Optional[float] = None
    wall_thickness_mm: Optional[float] = None
    flaw_length_mm: Optional[float] = None
    flaw_depth_mm: Optional[float] = None
    steel_grade: Optional[str] = None
    joint_factor: Optional[float] = None
    design_factor: Optional[float] = None
    temperature_factor: Optional[float] = None


class DigListEntry(BaseModel):
    anomaly_id: str
    distance_m: Optional[float] = None
    clock_position: Optional[str] = None
    depth_percent: Optional[float] = None
    erf: Optional[float] = None
    category: Literal["A", "B", "C"]
    reason: Optional[str] = None


class AddendumReport(BaseModel):
    header: ReportHeader
    erf_inputs: Optional[ERFInputs] = None
    dig_list: List[DigListEntry]


class IndustrialSafetyConclusion(BaseModel):
    header: ReportHeader
    compliance_statement: str
    remaining_life_years: Optional[float] = None
    expert_signatures: List[str]


class Questionnaire(BaseModel):
    header: ReportHeader


class ReportsBundle(BaseModel):
    questionnaire: Questionnaire
    express_report: ExpressReport
    final_report: FinalReport
    addendum_report: AddendumReport
    industrial_safety_conclusion: IndustrialSafetyConclusion


def _compute_erf(depth_mm: Optional[float], wall_thickness_mm: Optional[float]) -> Optional[float]:
    if depth_mm is None or wall_thickness_mm is None or wall_thickness_mm <= 0:
        return None
    return depth_mm / wall_thickness_mm


def _categorize_erf(erf: Optional[float]) -> str:
    if erf is None:
        return "C"
    if erf > 1.0:
        return "A"
    if erf >= 0.8:
        return "B"
    return "C"


def _depth_percent(depth_mm: Optional[float], wall_thickness_mm: Optional[float]) -> Optional[float]:
    if depth_mm is None or wall_thickness_mm is None or wall_thickness_mm <= 0:
        return None
    return (depth_mm / wall_thickness_mm) * 100


def _build_histogram(depth_values: List[float]) -> List[HistogramBin]:
    if not depth_values:
        return []
    max_depth = max(depth_values)
    if max_depth <= 0:
        return []
    bin_size = max_depth / 5 if max_depth > 5 else 1.0
    bins: List[HistogramBin] = []
    start = 0.0
    while start < max_depth:
        end = start + bin_size
        # include the max value in the last bin
        count = len([v for v in depth_values if (v >= start and (v < end or (end >= max_depth and v <= max_depth)))])
        bins.append(HistogramBin(bin_start_mm=start, bin_end_mm=end, count=count))
        start = end
    return bins


def _build_header(
    pipeline: Pipeline,
    inspections: List[Inspection],
    operator: Optional[str],
    diameter_mm: Optional[float],
    wall_thickness_mm: Optional[float],
    steel_grade: Optional[str],
    launcher_trap_length_mm: Optional[float],
    receiver_trap_length_mm: Optional[float],
) -> ReportHeader:
    latest_date = None
    if inspections:
        with_dates = [i.date.date() for i in inspections if i.date]
        latest_date = max(with_dates) if with_dates else None
    methods = sorted({str(i.method.value if hasattr(i.method, "value") else i.method) for i in inspections if i.method})
    return ReportHeader(
        pipeline_id=pipeline.pipeline_id,
        pipeline_name=pipeline.description,
        inspection_date=latest_date,
        operator=operator,
        diameter_mm=diameter_mm,
        wall_thickness_mm=wall_thickness_mm,
        steel_grade=steel_grade,
        launcher_trap_length_mm=launcher_trap_length_mm,
        receiver_trap_length_mm=receiver_trap_length_mm,
        required_methods=methods,
    )


@router.get("/{pipeline_id}", response_model=ReportsBundle)
def generate_reports(
    pipeline_id: str,
    operator: Optional[str] = None,
    diameter_mm: Optional[float] = None,
    wall_thickness_mm: Optional[float] = None,
    steel_grade: Optional[str] = None,
    launcher_trap_length_mm: Optional[float] = None,
    receiver_trap_length_mm: Optional[float] = None,
    db: Session = Depends(get_db),
) -> ReportsBundle:
    pipeline = db.get(Pipeline, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    objects = db.exec(select(Object).where(Object.pipeline_id == pipeline_id)).all()
    if not objects:
        raise HTTPException(status_code=404, detail="No objects found for pipeline")

    object_ids = [obj.object_id for obj in objects if obj.object_id is not None]
    inspections: List[Inspection] = []
    if object_ids:
        inspections = db.exec(select(Inspection).where(Inspection.object_id.in_(object_ids))).all()

    inspection_ids = [insp.inspection_id for insp in inspections if insp.inspection_id is not None]
    defects: List[Defect] = []
    if inspection_ids:
        defects = db.exec(select(Defect).where(Defect.inspection_id.in_(inspection_ids))).all()

    header = _build_header(
        pipeline=pipeline,
        inspections=inspections,
        operator=operator,
        diameter_mm=diameter_mm,
        wall_thickness_mm=wall_thickness_mm,
        steel_grade=steel_grade,
        launcher_trap_length_mm=launcher_trap_length_mm,
        receiver_trap_length_mm=receiver_trap_length_mm,
    )
    depth_values = [d.depth for d in defects if d.depth is not None]
    histogram = _build_histogram(depth_values)

    def defect_type_label(defect: Defect) -> Literal["metal_loss", "geometry"]:
        text = (defect.defect_type or "").lower()
        return "geometry" if "geo" in text or "dent" in text else "metal_loss"

    # Express report
    top_sorted = sorted(defects, key=lambda d: d.depth or 0, reverse=True)[:10]
    top_entries: List[TopDefectSummary] = []
    for idx, defect in enumerate(top_sorted, start=1):
        erf_val = _compute_erf(defect.depth, header.wall_thickness_mm)
        top_entries.append(
            TopDefectSummary(
                anomaly_id=f"DEF-{defect.defect_id or idx}",
                type=defect_type_label(defect),
                depth_mm=defect.depth,
                depth_percent=_depth_percent(defect.depth, header.wall_thickness_mm),
                length_mm=defect.length,
                clock_position=None,
                distance_m=None,
                erf=erf_val,
                immediate_action_required=_categorize_erf(erf_val) == "A",
            )
        )
    express_immediate = any(item.immediate_action_required for item in top_entries)

    # Final report data
    anomaly_count_geom = sum(1 for d in defects if defect_type_label(d) == "geometry")
    anomaly_count_metal = len(defects) - anomaly_count_geom
    defect_items: List[DefectItem] = []
    for idx, defect in enumerate(defects, start=1):
        erf_val = _compute_erf(defect.depth, header.wall_thickness_mm)
        defect_items.append(
            DefectItem(
                anomaly_id=f"DEF-{defect.defect_id or idx}",
                type=defect_type_label(defect),
                distance_m=None,
                clock_position=None,
                depth_mm=defect.depth,
                depth_percent=_depth_percent(defect.depth, header.wall_thickness_mm),
                length_mm=defect.length,
                width_mm=defect.width,
                erf=erf_val,
            )
        )

    visuals = VisualsData(
        map_image_url=None,
        xyz_profile=[(float(obj.object_id or idx), obj.lat, obj.lon) for idx, obj in enumerate(objects)],
        depth_histogram=histogram,
    )

    # Addendum: dig list sorted by category then ERF descending
    dig_list: List[DigListEntry] = []
    for idx, defect in enumerate(defects, start=1):
        erf_val = _compute_erf(defect.depth, header.wall_thickness_mm)
        category = _categorize_erf(erf_val)
        reason = "ERF > 1.0" if category == "A" else "0.8 < ERF < 1.0" if category == "B" else "Monitor"
        dig_list.append(
            DigListEntry(
                anomaly_id=f"DEF-{defect.defect_id or idx}",
                distance_m=None,
                clock_position=None,
                depth_percent=_depth_percent(defect.depth, header.wall_thickness_mm),
                erf=erf_val,
                category=category,  # type: ignore[arg-type]
                reason=reason,
            )
        )
    category_order = {"A": 0, "B": 1, "C": 2}
    dig_list.sort(key=lambda d: (category_order[d.category], -(d.erf or 0)))

    bundle = ReportsBundle(
        questionnaire=Questionnaire(header=header),
        express_report=ExpressReport(
            header=header,
            total_anomalies=len(defects),
            top_10_critical_defects=top_entries,
            immediate_action_required=express_immediate,
        ),
        final_report=FinalReport(
            header=header,
            total_length_inspected_km=None,
            total_weld_joints=None,
            anomaly_count_metal_loss=anomaly_count_metal,
            anomaly_count_geometry=anomaly_count_geom,
            defects=defect_items,
            visuals=visuals,
        ),
        addendum_report=AddendumReport(
            header=header,
            erf_inputs=ERFInputs(
                diameter_mm=header.diameter_mm,
                wall_thickness_mm=header.wall_thickness_mm,
                steel_grade=header.steel_grade,
            ),
            dig_list=dig_list,
        ),
        industrial_safety_conclusion=IndustrialSafetyConclusion(
            header=header,
            compliance_statement="Data derived from latest inspections; verify engineering calculations before issuance.",
            remaining_life_years=None,
            expert_signatures=[],
        ),
    )
    return bundle
