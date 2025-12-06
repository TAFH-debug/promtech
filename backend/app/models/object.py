from sqlmodel import SQLModel, Field, Column, Relationship
from sqlalchemy import Integer, Enum as SQLEnum
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import enum

if TYPE_CHECKING:
    from app.models.diagnostic import Diagnostic


class ObjectType(str, enum.Enum):
    CRANE = "crane"
    COMPRESSOR = "compressor"
    PIPELINE_SECTION = "pipeline section"


class ObjectBase(SQLModel):
    object_name: str = Field(description="Наименование оборудования или участка трубы")
    object_type: ObjectType = Field(
        description="Тип объекта: crane / compressor / pipeline section",
        sa_column=Column(SQLEnum(ObjectType))
    )
    pipeline_id: Optional[str] = Field(default=None, description="Идентификатор условного трубопровода")
    lat: float = Field(description="Географическая широта")
    lon: float = Field(description="Географическая долгота")
    year: Optional[int] = Field(default=None, description="Год выпуска / ввода в эксплуатацию")
    material: Optional[str] = Field(default=None, description="Марка стали или материала")


class Object(ObjectBase, table=True):
    __tablename__ = "objects"
    
    object_id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Идентификатор объекта"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to Diagnostics
    diagnostics: List["Diagnostic"] = Relationship(back_populates="object")


class ObjectCreate(ObjectBase):
    pass


class ObjectUpdate(SQLModel):
    object_name: Optional[str] = None
    object_type: Optional[ObjectType] = None
    pipeline_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    year: Optional[int] = None
    material: Optional[str] = None


class ObjectRead(ObjectBase):
    object_id: int
    created_at: datetime
    updated_at: datetime

