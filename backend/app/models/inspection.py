from datetime import datetime
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlmodel import Column, Field, Relationship, SQLModel

from app.models.diagnostic import DiagnosticMethod, MLLabel, QualityGrade

if TYPE_CHECKING:
    from app.models.defect import Defect
    from app.models.object import Object


class Inspection(SQLModel, table=True):
    __tablename__ = "inspections"

    inspection_id: Optional[int] = Field(default=None, primary_key=True)
    object_id: int = Field(foreign_key="objects.object_id", description="Inspected object")
    date: datetime = Field(description="Inspection date and time")
    method: DiagnosticMethod = Field(sa_column=Column(SQLEnum(DiagnosticMethod)))
    temperature: Optional[float] = Field(default=None, description="Ambient temperature")
    humidity: Optional[float] = Field(default=None, description="Ambient humidity")
    illumination: Optional[float] = Field(default=None, description="Ambient illumination")
    quality_grade: Optional[QualityGrade] = Field(
        default=None, description="Quality grade", sa_column=Column(SQLEnum(QualityGrade))
    )
    ml_label: Optional[MLLabel] = Field(
        default=None, description="ML label", sa_column=Column(SQLEnum(MLLabel))
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    object: Optional["Object"] = Relationship(back_populates="inspections")
    defects: List["Defect"] = Relationship(back_populates="inspection")
