from app.models.object import Object, ObjectCreate, ObjectUpdate, ObjectRead, ObjectType
from app.models.pipeline import Pipeline
from app.models.inspection import Inspection
from app.models.defect import Defect
from app.models.diagnostic import (
    Diagnostic,
    DiagnosticCreate,
    DiagnosticUpdate,
    DiagnosticRead,
    DiagnosticMethod,
    QualityGrade,
    MLLabel,
)

# Import all models for Alembic
__all__ = [
    "Object",
    "ObjectCreate",
    "ObjectUpdate",
    "ObjectRead",
    "ObjectType",
    "Pipeline",
    "Inspection",
    "Defect",
    "Diagnostic",
    "DiagnosticCreate",
    "DiagnosticUpdate",
    "DiagnosticRead",
    "DiagnosticMethod",
    "QualityGrade",
    "MLLabel",
]

