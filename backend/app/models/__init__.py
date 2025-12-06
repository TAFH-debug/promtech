from app.models.object import Object, ObjectCreate, ObjectUpdate, ObjectRead, ObjectType
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
    "Diagnostic",
    "DiagnosticCreate",
    "DiagnosticUpdate",
    "DiagnosticRead",
    "DiagnosticMethod",
    "QualityGrade",
    "MLLabel",
]

