from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.inspection import Inspection


class Defect(SQLModel, table=True):
    __tablename__ = "defects"

    defect_id: Optional[int] = Field(default=None, primary_key=True)
    inspection_id: int = Field(foreign_key="inspections.inspection_id", description="Parent inspection")
    defect_type: Optional[str] = Field(default=None, description="Type of defect")
    depth: Optional[float] = Field(default=None, description="Defect depth")
    length: Optional[float] = Field(default=None, description="Defect length")
    width: Optional[float] = Field(default=None, description="Defect width")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    inspection: Optional["Inspection"] = Relationship(back_populates="defects")
