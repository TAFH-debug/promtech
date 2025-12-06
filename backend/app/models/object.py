from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import enum

from sqlalchemy import Column, Enum as SQLEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.diagnostic import Diagnostic
    from app.models.pipeline import Pipeline
    from app.models.inspection import Inspection


class ObjectType(str, enum.Enum):
    CRANE = "crane"
    COMPRESSOR = "compressor"
    PIPELINE_SECTION = "pipeline section"


class ObjectBase(SQLModel):
    object_name: str = Field(description="Name of the object")
    object_type: ObjectType = Field(
        description="Type of object: crane / compressor / pipeline section",
        sa_column=Column(SQLEnum(ObjectType)),
    )
    pipeline_id: Optional[str] = Field(
        default=None,
        description="Pipeline identifier",
        foreign_key="pipelines.pipeline_id",
    )
    lat: float = Field(description="Latitude")
    lon: float = Field(description="Longitude")
    year: Optional[int] = Field(default=None, description="Construction or installation year")
    material: Optional[str] = Field(default=None, description="Material of the object")


class Object(ObjectBase, table=True):
    __tablename__ = "objects"

    object_id: Optional[int] = Field(default=None, primary_key=True, description="Object primary key")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    pipeline: Optional["Pipeline"] = Relationship(back_populates="objects")
    inspections: List["Inspection"] = Relationship(back_populates="object")
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
