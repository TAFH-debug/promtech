from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Enum as SQLEnum
from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
import enum

if TYPE_CHECKING:
    from app.models.object import Object


class DiagnosticMethod(str, enum.Enum):
    """Методы контроля"""
    VIK = "VIK"
    PVK = "PVK"
    MPK = "MPK"
    UZK = "UZK"
    RGK = "RGK"
    TVK = "TVK"
    VIBRO = "VIBRO"
    MFL = "MFL"
    TFI = "TFI"
    GEO = "GEO"
    UTWM = "UTWM"


class QualityGrade(str, enum.Enum):
    """Оценка качества"""
    SATISFACTORY = "удовлетворительно"
    ACCEPTABLE = "допустимо"
    REQUIRES_ACTION = "требует мер"
    UNACCEPTABLE = "недопустимо"


class MLLabel(str, enum.Enum):
    """Целевой класс для ML"""
    NORMAL = "normal"
    MEDIUM = "medium"
    HIGH = "high"


class DiagnosticBase(SQLModel):
    object_id: int = Field(
        foreign_key="objects.object_id",
        description="Ссылка на объект"
    )
    method: DiagnosticMethod = Field(
        description="Метод контроля",
        sa_column=Column(SQLEnum(DiagnosticMethod))
    )
    date: datetime = Field(description="Дата проведения контроля")
    temperature: Optional[float] = Field(default=None, description="Температура воздуха")
    humidity: Optional[float] = Field(default=None, description="Влажность")
    illumination: Optional[float] = Field(default=None, description="Освещенность")
    defect_found: bool = Field(default=False, description="Признак дефекта")
    defect_description: Optional[str] = Field(default=None, description="Описание дефекта")
    quality_grade: Optional[QualityGrade] = Field(
        default=None,
        description="Оценка качества",
        sa_column=Column(SQLEnum(QualityGrade))
    )
    param1: Optional[float] = Field(default=None, description="Параметр 1 (глубина, виброскорость, толщина и т.п.)")
    param2: Optional[float] = Field(default=None, description="Параметр 2")
    param3: Optional[float] = Field(default=None, description="Параметр 3")
    ml_label: Optional[MLLabel] = Field(
        default=None,
        description="Целевой класс для ML",
        sa_column=Column(SQLEnum(MLLabel))
    )


class Diagnostic(DiagnosticBase, table=True):
    __tablename__ = "diagnostics"
    
    diag_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Идентификатор записи"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to Object
    object: Optional["Object"] = Relationship(back_populates="diagnostics")


class DiagnosticCreate(DiagnosticBase):
    pass


class DiagnosticUpdate(SQLModel):
    object_id: Optional[int] = None
    method: Optional[DiagnosticMethod] = None
    date: Optional[datetime] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    illumination: Optional[float] = None
    defect_found: Optional[bool] = None
    defect_description: Optional[str] = None
    quality_grade: Optional[QualityGrade] = None
    param1: Optional[float] = None
    param2: Optional[float] = None
    param3: Optional[float] = None
    ml_label: Optional[MLLabel] = None


class DiagnosticRead(DiagnosticBase):
    diag_id: int
    created_at: datetime
    updated_at: datetime

